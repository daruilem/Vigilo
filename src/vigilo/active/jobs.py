"""Active scans as background jobs, followed live.

An active scan takes several minutes, longer than a browser should keep one request
open with nothing to show. So starting a scan returns a job id straight away, and the
browser follows the job's events (the same `plan` / `step` / `report` / `failure` events
as the passive scan). Events are kept, so a page that reconnects sees the whole log.

Jobs live in memory only and are forgotten an hour after they finish. Limits:
- one active scan at a time per website,
- a small number of active scans at the same time overall (the tools are heavy).
"""

from __future__ import annotations

import asyncio
import logging
import secrets
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from vigilo import errors, scoring
from vigilo.active.findings import CHECK, TOOL_NAMES, to_findings
from vigilo.active.parsers import ToolResult, parse_nuclei, parse_zap
from vigilo.active.runner import Runner, ScanPlan, ToolFailed, docker_runner, tool_runs, zap_report
from vigilo.i18n import localize_event, localize_report, translate
from vigilo.models import Finding, ScanReport, Status
from vigilo.signing import sign

logger = logging.getLogger(__name__)

KEEP_SECONDS = 3600

PROOF_STEP = {"id": "proof", "label": "Proof of ownership checked again"}
STEP_LABELS = {
    "nuclei": "Known vulnerabilities and exposed files (Nuclei)",
    "zap": "Crawl of the site and passive analysis (OWASP ZAP)",
}
ANALYSIS_STEP = {"id": "analysis", "label": "Analysis of the results"}

Event = tuple[str, dict[str, Any]]


class JobError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class Job:
    id: str
    domain: str
    lang: str
    created: float
    events: list[Event] = field(default_factory=list)
    finished_at: float | None = None
    task: asyncio.Task[None] | None = None
    _changed: asyncio.Condition = field(default_factory=asyncio.Condition)

    @property
    def running(self) -> bool:
        return self.finished_at is None

    async def emit(self, name: str, data: dict[str, Any]) -> None:
        async with self._changed:
            self.events.append((name, data))
            self._changed.notify_all()

    async def finish(self, now: float) -> None:
        async with self._changed:
            self.finished_at = now
            self._changed.notify_all()

    async def follow(self) -> AsyncIterator[Event]:
        """Every event so far, then each new one, until the job is finished."""
        seen = 0
        while True:
            async with self._changed:
                while seen >= len(self.events) and self.running:
                    await self._changed.wait()
                batch = self.events[seen:]
                seen = len(self.events)
                done = not self.running
            for event in batch:
                yield event
            if done and seen >= len(self.events):
                return


def _parse(tool: str, output: str, domain: str) -> list[ToolResult]:
    if tool == "nuclei":
        return parse_nuclei(output, domain)
    return parse_zap(zap_report(output), domain)


def _tool_error(tool: str) -> Finding:
    label = STEP_LABELS[tool]
    return Finding(
        id=f"{CHECK}.{tool}.error",
        check=CHECK,
        title=label,
        headline=f"{label}: could not be checked",
        status=Status.ERROR,
        description="This check could not be completed, so its results are missing.",
        evidence={"tool": TOOL_NAMES.get(tool, tool)},
    )


class JobManager:
    def __init__(
        self,
        capacity: int,
        runner: Runner = docker_runner,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.capacity = capacity
        self.runner = runner
        self._clock = clock
        self._jobs: dict[str, Job] = {}

    def get(self, job_id: str) -> Job | None:
        self._forget_old()
        return self._jobs.get(job_id)

    def check_can_start(self, domain: str) -> None:
        """Raise JobError if a scan of `domain` cannot start now. No side effect."""
        self._forget_old()
        running = [job for job in self._jobs.values() if job.running]
        if any(job.domain == domain for job in running):
            raise JobError("active_already_running", errors.ACTIVE_ALREADY_RUNNING)
        if len(running) >= self.capacity:
            raise JobError("active_busy", errors.ACTIVE_BUSY)

    def start(self, plan: ScanPlan, lang: str) -> Job:
        self.check_can_start(plan.domain)
        job = Job(
            id=secrets.token_urlsafe(18), domain=plan.domain, lang=lang, created=self._clock()
        )
        self._jobs[job.id] = job
        job.task = asyncio.create_task(self._run(job, plan))
        return job

    def _forget_old(self) -> None:
        now = self._clock()
        for job_id, job in list(self._jobs.items()):
            if job.finished_at is not None and now - job.finished_at > KEEP_SECONDS:
                del self._jobs[job_id]

    async def _progress(self, job: Job, event: dict[str, Any]) -> None:
        await job.emit("progress", localize_event(event, job.lang))

    async def _run(self, job: Job, plan: ScanPlan) -> None:
        started = datetime.now(timezone.utc)
        runs = tool_runs(plan)
        steps = [PROOF_STEP] + [{"id": r.tool, "label": STEP_LABELS[r.tool]} for r in runs]
        try:
            await self._progress(job, {"type": "plan", "steps": [*steps, ANALYSIS_STEP]})
            await self._progress(job, {"type": "step", "id": "proof", "state": "done"})

            results: list[ToolResult] = []
            failed: list[str] = []
            for run in runs:
                await self._progress(job, {"type": "step", "id": run.tool, "state": "running"})
                try:
                    output = await self.runner(run)
                    results += _parse(run.tool, output, plan.domain)
                except ToolFailed as exc:
                    logger.warning("Active scan of %s: %s", plan.domain, exc)
                    failed.append(run.tool)
                    await self._progress(job, {"type": "step", "id": run.tool, "state": "failed"})
                    continue
                await self._progress(job, {"type": "step", "id": run.tool, "state": "done"})

            if len(failed) == len(runs):
                await job.emit("failure", self._failure("active_failed", errors.ACTIVE_FAILED, job))
                return

            await self._progress(job, {"type": "step", "id": "analysis", "state": "running"})
            findings = to_findings(results) + [_tool_error(tool) for tool in failed]
            value = scoring.score(findings)
            report = ScanReport(
                target=plan.domain,
                kind="active",
                started_at=started,
                finished_at=datetime.now(timezone.utc),
                score=value,
                grade=scoring.grade(value),
                findings=findings,
            )
            await self._progress(job, {"type": "step", "id": "analysis", "state": "done"})
            signed = sign(localize_report(report, job.lang))
            await job.emit("report", signed.model_dump(mode="json"))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Unexpected error during the active scan of %s", plan.domain)
            await job.emit("failure", self._failure("internal", errors.INTERNAL, job))
        finally:
            await job.finish(self._clock())

    @staticmethod
    def _failure(code: str, message: str, job: Job) -> dict[str, str]:
        return {"code": code, "message": translate(message, job.lang) or message}
