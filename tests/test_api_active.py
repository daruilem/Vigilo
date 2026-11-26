import json

import pytest
from fastapi.testclient import TestClient
from test_jobs import fake_runner

from vigilo import api
from vigilo.active.jobs import JobManager
from vigilo.errors import ScanError
from vigilo.lab import parse_lab_targets
from vigilo.ownership import Method, issue_pass

client = TestClient(api.app)
DOMAIN = "shop.example"


@pytest.fixture(autouse=True)
def active(monkeypatch, tmp_path):
    """Active scan on, fresh limits and jobs, no real network, consent log in a file."""
    monkeypatch.setattr(api, "ACTIVE_ENABLED", True)
    monkeypatch.setattr(api, "active_jobs", JobManager(1, fake_runner))
    monkeypatch.setattr(api, "LAB_TARGETS", {})
    api.active_limiter.reset()
    api.active_target_limiter.reset()
    calls = []

    async def verified(domain, token, method, **kwargs):
        calls.append((domain, token, method, kwargs))
        return issue_pass(domain, method)

    async def resolved(host):
        return ["2001:db8::1", "203.0.113.7"]

    monkeypatch.setattr(api, "verify_ownership", verified)

    async def not_hosted(domain):
        return None

    monkeypatch.setattr(api, "_hosted_platform", not_hosted)
    monkeypatch.setattr(api, "ensure_public_host", resolved)
    log = tmp_path / "consent.jsonl"
    monkeypatch.setenv("VIGILO_CONSENT_LOG", str(log))
    return calls, log


def start(**overrides):
    body = {
        "target": DOMAIN,
        "token": "the-code",
        "ownership_pass": issue_pass(DOMAIN, Method.FILE).token,
        "accept_terms": True,
    }
    body.update(overrides)
    return client.post("/api/v1/active-scans", json=body)


def stream(job_id):
    response = client.get(f"/api/v1/active-scans/{job_id}/stream")
    events = []
    for block in response.text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines() if not line.startswith(":"))
        if lines:
            events.append((lines["event"], json.loads(lines["data"])))
    return events


def test_off_by_default(monkeypatch):
    monkeypatch.setattr(api, "ACTIVE_ENABLED", False)
    assert start().status_code == 404


def test_terms_must_be_accepted():
    response = start(accept_terms=False)
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "terms_not_accepted"


@pytest.mark.parametrize(
    "ownership_pass",
    ["forged", "file.9999999999.0000", issue_pass("other.example", Method.DNS).token],
)
def test_a_valid_pass_for_this_exact_host_is_required(ownership_pass):
    response = start(ownership_pass=ownership_pass)
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "not_verified"


def test_the_proof_is_checked_again_before_starting(active, monkeypatch):
    async def gone(domain, token, method, **kwargs):
        raise ScanError("We could not find the file.", "file_not_found")

    monkeypatch.setattr(api, "verify_ownership", gone)
    response = start()
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "file_not_found"


def test_a_scan_starts_logs_consent_and_streams_its_report(active):
    calls, log = active
    response = start()
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    assert calls == [(DOMAIN, "the-code", Method.FILE, {})]

    entry = json.loads(log.read_text(encoding="utf-8"))
    assert entry["event"] == "active_scan_started"
    assert entry["domain"] == DOMAIN and entry["proof"] == "file" and entry["job"] == job_id

    events = stream(job_id)
    assert events[-1][0] == "report"
    assert events[-1][1]["kind"] == "active"


def test_tools_are_pinned_to_the_validated_ipv4_address(monkeypatch):
    plans = []
    manager = JobManager(1, fake_runner)
    real_start = manager.start
    monkeypatch.setattr(api, "active_jobs", manager)
    monkeypatch.setattr(
        manager, "start", lambda plan, lang: plans.append(plan) or real_start(plan, lang)
    )
    assert start().status_code == 202
    assert plans[0].pinned_address == "203.0.113.7"
    assert plans[0].target_url == "https://shop.example/"


def test_daily_limits(monkeypatch):
    monkeypatch.setattr(api, "active_target_limiter", api.RateLimiter(1, 86400))
    assert start().status_code == 202
    # Same site again (once the first job is done): refused by the per-site daily limit.
    monkeypatch.setattr(api, "active_jobs", JobManager(1, fake_runner))
    response = start()
    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "target_rate_limited"


def test_lab_hosts_use_the_lab_network(active, monkeypatch):
    calls, _ = active
    monkeypatch.setattr(api, "LAB_TARGETS", parse_lab_targets("juice.lab=http://127.0.0.1:8080"))
    plans = []
    manager = JobManager(1, fake_runner)
    real_start = manager.start
    monkeypatch.setattr(api, "active_jobs", manager)
    monkeypatch.setattr(
        manager, "start", lambda plan, lang: plans.append(plan) or real_start(plan, lang)
    )
    response = start(target="juice.lab", ownership_pass=issue_pass("juice.lab", Method.FILE).token)
    assert response.status_code == 202
    assert calls[0][3]["base_url"] == "http://127.0.0.1:8080"
    assert plans[0].network == "vigilo-lab" and plans[0].pinned_address is None


def test_unknown_job():
    assert stream("does-not-exist") == [
        ("failure", {"code": "active_not_found", "message": api.errors.ACTIVE_NOT_FOUND})
    ]
