"""Runs all checks against a target and builds the report.

A scan has a first "connect" step that fetches the home page once. It decides whether a
report is possible at all (site reachable, no redirect loop, no timeout) and hands the
response to the checks, so each resource is requested only once.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence
from datetime import datetime, timezone
from typing import Any

import httpx

from vigilo import errors, guidance, scoring
from vigilo.checks import ALL_CHECKS, Check, ScanContext
from vigilo.errors import ScanError
from vigilo.models import Finding, ScanReport, Status
from vigilo.net import fetch_page, make_client
from vigilo.target import Target, ensure_public_host, parse_target

logger = logging.getLogger(__name__)

# Progress events: {"type": "plan", "steps": [...]} once, then
# {"type": "step", "id": ..., "state": "running" | "done" | "failed"} per step.
Event = dict[str, Any]
EventHandler = Callable[[Event], Awaitable[None]]

CONNECT_STEP = {"id": "connect", "label": "Connect and load the home page"}


async def _noop(_: Event) -> None:
    return None


async def scan(
    raw_target: str,
    *,
    allow_private: bool = False,
    checks: Sequence[Check] | None = None,
    on_event: EventHandler | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> ScanReport:
    """Scan `raw_target`. Raises `ScanError` (or its subclass `TargetError`) on failure."""
    emit = on_event or _noop
    selected = list(checks or ALL_CHECKS)

    target = parse_target(raw_target)
    addresses: tuple[str, ...] = ()
    if not allow_private:
        addresses = tuple(await ensure_public_host(target.hostname))

    await emit(
        {
            "type": "plan",
            "steps": [CONNECT_STEP] + [{"id": c.name, "label": c.label} for c in selected],
        }
    )

    started = datetime.now(timezone.utc)
    async with make_client(allow_private=allow_private, transport=transport) as http:
        await emit({"type": "step", "id": "connect", "state": "running"})
        try:
            homepage = await connect(http, target)
        except ScanError:
            await emit({"type": "step", "id": "connect", "state": "failed"})
            raise
        await emit({"type": "step", "id": "connect", "state": "done"})

        ctx = ScanContext(
            target=target,
            http=http,
            allow_private=allow_private,
            homepage=homepage,
            addresses=addresses,
            html=_html_of(homepage),
        )
        results = await asyncio.gather(*(_run_check(c, ctx, emit) for c in selected))

    findings = [guidance.enrich(f, target.hostname) for result in results for f in result]
    value = scoring.score(findings)
    return ScanReport(
        target=target.hostname,
        started_at=started,
        finished_at=datetime.now(timezone.utc),
        score=value,
        grade=scoring.grade(value),
        findings=findings,
    )


async def connect(http: httpx.AsyncClient, target: Target) -> httpx.Response | None:
    """Fetch the home page. Returns None when only a certificate problem blocks HTTPS,
    because that is a finding to report, not a reason to stop."""
    try:
        return await fetch_page(http, target.https_url)
    except httpx.TooManyRedirects as exc:
        raise ScanError(errors.TOO_MANY_REDIRECTS, "too_many_redirects") from exc
    except httpx.TimeoutException as exc:
        raise ScanError(errors.TIMEOUT, "timeout") from exc
    except httpx.ConnectError as exc:
        if "CERTIFICATE_VERIFY_FAILED" in str(exc):
            return None
        https_error: Exception = exc

    # HTTPS is not answering at all: the site may still work over plain HTTP.
    try:
        await fetch_page(http, target.http_url)
    except httpx.TooManyRedirects as exc:
        raise ScanError(errors.TOO_MANY_REDIRECTS, "too_many_redirects") from exc
    except httpx.TimeoutException as exc:
        raise ScanError(errors.TIMEOUT, "timeout") from exc
    except httpx.TransportError:
        raise ScanError(errors.UNREACHABLE, "unreachable") from https_error
    return None


MAX_HTML_BYTES = 2_000_000


def _html_of(response: httpx.Response | None) -> str:
    if response is None or response.status_code != 200:
        return ""
    if "html" not in response.headers.get("content-type", "").lower():
        return ""
    return response.text[:MAX_HTML_BYTES]


async def _run_check(check: Check, ctx: ScanContext, emit: EventHandler) -> list[Finding]:
    await emit({"type": "step", "id": check.name, "state": "running"})
    try:
        findings = await check.run(ctx)
    except Exception as exc:  # one broken check must never break the whole scan
        logger.warning("Check %s failed on %s: %r", check.name, ctx.target.hostname, exc)
        await emit({"type": "step", "id": check.name, "state": "failed"})
        return [
            Finding(
                id=f"{check.name}.error",
                check=check.name,
                title=check.label,
                headline=f"{check.label}: could not be checked",
                status=Status.ERROR,
                description="This check could not be completed, so its results are missing.",
                evidence={"error": type(exc).__name__},
            )
        ]
    await emit({"type": "step", "id": check.name, "state": "done"})
    return findings
