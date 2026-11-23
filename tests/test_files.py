import asyncio

import httpx
import pytest

from vigilo.checks.files import NOT_READ_NOTE, Probe, evaluate_probes, is_exposed, probe_path
from vigilo.models import Severity, Status


def probe(path="/.git/HEAD", status=200, size=23, content_type="text/plain"):
    return Probe(path=path, status=status, size=size, content_type=content_type)


@pytest.mark.parametrize(
    ("p", "exposed"),
    [
        (probe(), True),
        (probe(size=None, content_type="application/octet-stream"), True),
        (probe(status=404), False),
        (probe(status=403), False),
        (probe(content_type="text/html; charset=utf-8"), False),  # soft 404 page
        (probe(size=0), False),
    ],
)
def test_is_exposed(p, exposed):
    assert is_exposed(p) is exposed


def test_exposed_git_folder_is_reported_without_content():
    findings = evaluate_probes([probe(), probe("/.env", status=404)])
    assert [f.id for f in findings] == ["files.git"]
    git = findings[0]
    assert git.status is Status.FAIL
    assert git.severity is Severity.HIGH
    assert git.observed[0].label == "GET /.git/HEAD"
    assert git.observed[0].value == "200 OK · 23 bytes"
    assert git.note == NOT_READ_NOTE


def test_exposed_env_file_is_critical():
    findings = evaluate_probes([probe("/.env", size=512)])
    assert findings[0].id == "files.env"
    assert findings[0].severity is Severity.CRITICAL


def test_nothing_exposed_gives_one_passing_finding():
    findings = evaluate_probes([probe(status=404), probe("/.env", status=404)])
    assert len(findings) == 1
    assert findings[0].id == "files.none"
    assert findings[0].status is Status.PASS


def test_probe_reads_status_size_and_type_only():
    def handler(request):
        assert request.method == "GET"
        return httpx.Response(
            200,
            headers={"Content-Length": "4", "Content-Type": "text/plain"},
            content=b"SECR",
        )

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            return await probe_path(http, "https://example.com/.env", "/.env")

    result = asyncio.run(go())
    assert result == Probe(path="/.env", status=200, size=4, content_type="text/plain")
