import asyncio

import httpx
import pytest

from vigilo.checks.base import Check, ScanContext
from vigilo.errors import ScanError
from vigilo.models import Finding, Severity, Status
from vigilo.scanner import scan


class LowFindingCheck(Check):
    name = "sample"
    label = "Sample check"
    description = "always reports one low-severity failure"

    async def run(self, ctx: ScanContext) -> list[Finding]:
        assert ctx.homepage is not None and ctx.homepage.status_code == 200
        return [
            Finding(
                id="sample.low",
                check=self.name,
                title="ok",
                status=Status.FAIL,
                severity=Severity.LOW,
                description="",
            )
        ]


class BrokenCheck(Check):
    name = "broken"
    label = "Broken check"
    description = "always crashes"

    async def run(self, ctx: ScanContext) -> list[Finding]:
        raise RuntimeError("boom")


def ok_site(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, text="<html></html>")


def run_scan(handler, checks=None, events=None):
    async def on_event(event):
        if events is not None:
            events.append(event)

    return asyncio.run(
        scan(
            "example.com",
            allow_private=True,
            checks=checks or [LowFindingCheck()],
            on_event=on_event,
            transport=httpx.MockTransport(handler),
        )
    )


def test_a_crashing_check_becomes_an_error_finding():
    events = []
    report = run_scan(ok_site, [LowFindingCheck(), BrokenCheck()], events)

    statuses = {f.id: f.status for f in report.findings}
    assert statuses == {"sample.low": Status.FAIL, "broken.error": Status.ERROR}
    assert report.score == 97
    assert report.grade == "A"
    assert report.target == "example.com"

    assert events[0]["type"] == "plan"
    assert [s["id"] for s in events[0]["steps"]] == ["connect", "sample", "broken"]
    states = {(e["id"], e["state"]) for e in events if e["type"] == "step"}
    assert ("connect", "done") in states
    assert ("sample", "done") in states
    assert ("broken", "failed") in states


def test_timeout_stops_the_scan():
    def handler(request):
        raise httpx.ConnectTimeout("timed out", request=request)

    with pytest.raises(ScanError) as exc:
        run_scan(handler)
    assert exc.value.code == "timeout"


def test_redirect_loop_stops_the_scan():
    def handler(request):
        return httpx.Response(302, headers={"Location": str(request.url)})

    with pytest.raises(ScanError) as exc:
        run_scan(handler)
    assert exc.value.code == "too_many_redirects"


def test_unreachable_site_stops_the_scan():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(ScanError) as exc:
        run_scan(handler)
    assert exc.value.code == "unreachable"


def test_invalid_certificate_does_not_stop_the_scan():
    class NoHomepageCheck(Check):
        name = "cert"
        label = "cert"
        description = ""

        async def run(self, ctx):
            assert ctx.homepage is None
            return []

    def handler(request):
        if request.url.scheme == "https":
            raise httpx.ConnectError(
                "[SSL: CERTIFICATE_VERIFY_FAILED] certificate has expired", request=request
            )
        return httpx.Response(200)

    report = run_scan(handler, [NoHomepageCheck()])
    assert report.findings == []
