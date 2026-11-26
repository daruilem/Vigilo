import asyncio
from pathlib import Path

import pytest

from vigilo.active.jobs import JobError, JobManager
from vigilo.active.runner import ZAP_REPORT_MARKER, ScanPlan, ToolFailed, ToolRun
from vigilo.models import ScanReport, Status
from vigilo.signing import verify

FIXTURES = Path(__file__).parent / "fixtures" / "active"
PLAN = ScanPlan(
    domain="shop.example", target_url="https://shop.example/", pinned_address="203.0.113.7"
)


def recorded_output(run: ToolRun) -> str:
    if run.tool == "nuclei":
        return (FIXTURES / "nuclei.jsonl").read_text(encoding="utf-8")
    report = (FIXTURES / "zap.json").read_text(encoding="utf-8")
    return f"ZAP log...\n{ZAP_REPORT_MARKER}\n{report}"


def runner_failing(*tools: str):
    async def run(tool_run: ToolRun) -> str:
        if tool_run.tool in tools:
            raise ToolFailed(tool_run.tool, "exit code 1")
        return recorded_output(tool_run)

    return run


async def fake_runner(run: ToolRun) -> str:
    return recorded_output(run)


async def run_job(manager: JobManager, lang: str = "en"):
    job = manager.start(PLAN, lang)
    events = [event async for event in job.follow()]
    return job, events


def test_a_scan_reports_progress_then_a_signed_active_report():
    async def go():
        return await run_job(JobManager(1, fake_runner))

    job, events = asyncio.run(go())
    names = [name for name, _ in events]
    assert names[0] == "progress" and names[-1] == "report"
    plan = events[0][1]
    assert [s["id"] for s in plan["steps"]] == ["proof", "nuclei", "zap", "analysis"]
    steps = [(d["id"], d["state"]) for n, d in events if n == "progress" and d["type"] == "step"]
    assert ("nuclei", "done") in steps and ("zap", "done") in steps

    report = ScanReport.model_validate(events[-1][1])
    assert report.kind == "active"
    assert report.target == "shop.example"
    assert verify(report)
    assert report.findings and all(f.check == "active" for f in report.findings)
    assert not job.running


def test_a_failed_tool_is_reported_and_the_other_results_kept():
    async def go():
        return await run_job(JobManager(1, runner_failing("zap")))

    _, events = asyncio.run(go())
    assert ("progress", {"type": "step", "id": "zap", "state": "failed"}) in events
    report = ScanReport.model_validate(events[-1][1])
    errors = [f for f in report.findings if f.status is Status.ERROR]
    assert [f.id for f in errors] == ["active.zap.error"]
    assert any(f.status is Status.FAIL for f in report.findings)


def test_when_every_tool_fails_there_is_no_report():
    async def go():
        return await run_job(JobManager(1, runner_failing("nuclei", "zap")))

    _, events = asyncio.run(go())
    name, data = events[-1]
    assert name == "failure" and data["code"] == "active_failed"


def test_events_are_translated():
    async def go():
        return await run_job(JobManager(1, fake_runner), lang="de")

    _, events = asyncio.run(go())
    labels = [s["label"] for s in events[0][1]["steps"]]
    assert "Auswertung der Ergebnisse" in labels


def test_one_scan_per_site_and_a_global_capacity():
    async def go():
        started = asyncio.Event()

        async def slow(run: ToolRun) -> str:
            started.set()
            await asyncio.sleep(10)
            return ""

        manager = JobManager(1, slow)
        job = manager.start(PLAN, "en")
        await started.wait()
        with pytest.raises(JobError) as same_site:
            manager.check_can_start("shop.example")
        with pytest.raises(JobError) as other_site:
            manager.check_can_start("other.example")
        assert job.task is not None
        job.task.cancel()
        return same_site.value.code, other_site.value.code

    assert asyncio.run(go()) == ("active_already_running", "active_busy")


def test_a_late_follower_sees_the_whole_log_and_jobs_are_forgotten():
    clock = [1000.0]

    async def go():
        manager = JobManager(1, fake_runner, clock=lambda: clock[0])
        job, first = await run_job(manager)
        again = [event async for event in job.follow()]
        assert again == first
        clock[0] += 3601
        return manager.get(job.id)

    assert asyncio.run(go()) is None
