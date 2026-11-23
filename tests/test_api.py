from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from vigilo import api
from vigilo.models import ScanReport
from vigilo.scanner import CONNECT_STEP

client = TestClient(api.app)

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


async def fake_scan(target, on_event=None):
    if on_event:
        await on_event({"type": "plan", "steps": [CONNECT_STEP]})
    return ScanReport(
        target=target, started_at=NOW, finished_at=NOW, score=100, grade="A", findings=[]
    )


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    api.limiter.reset()
    api.target_limiter.reset()
    api.slots.active = 0
    monkeypatch.setattr(api, "scan", fake_scan)
    yield
    api.limiter.reset()
    api.target_limiter.reset()


def post(target="example.com", authorized=True, **kwargs):
    return client.post("/api/v1/scans", json={"target": target, "authorized": authorized}, **kwargs)


def test_health_reveals_nothing():
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


def test_scan_returns_a_report():
    response = post()
    assert response.status_code == 200
    assert response.json()["grade"] == "A"
    assert api.slots.active == 0  # the slot is released


def test_scan_requires_explicit_authorization():
    response = post(authorized=False)
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "not_authorized"


def test_invalid_target_is_rejected_with_a_code():
    response = post("192.168.1.1")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "invalid_target"
    assert "domain name" in detail["message"]


def test_rate_limit_per_client(monkeypatch):
    monkeypatch.setattr(api.limiter, "max_events", 1)
    assert post("one.example").status_code == 200
    response = post("two.example")
    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "rate_limited"


def test_rate_limit_per_target_site(monkeypatch):
    monkeypatch.setattr(api.target_limiter, "max_events", 1)
    assert post("shop.example").status_code == 200
    response = post("https://shop.example/other-page")
    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "target_rate_limited"


def test_busy_when_all_slots_are_taken(monkeypatch):
    monkeypatch.setattr(api.slots, "active", api.slots.capacity)
    response = post()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "busy"


def test_spoofed_forwarded_for_is_ignored_without_trusted_proxies(monkeypatch):
    monkeypatch.setattr(api.limiter, "max_events", 1)
    assert post("a.example", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    # A different forged address must not give a fresh quota.
    response = post("b.example", headers={"X-Forwarded-For": "2.2.2.2"})
    assert response.status_code == 429


def test_security_headers_on_every_response():
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Content-Security-Policy"].startswith("default-src 'none'")
    assert response.headers["Cache-Control"] == "no-store"


def test_api_docs_are_disabled_by_default():
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_stream_sends_progress_then_report():
    response = client.get(
        "/api/v1/scans/stream", params={"target": "example.com", "authorized": "true"}
    )
    assert response.headers["content-type"].startswith("text/event-stream")
    text = response.text
    assert text.index("event: progress") < text.index("event: report")
    assert api.slots.active == 0


def test_stream_sends_failures_as_events():
    response = client.get("/api/v1/scans/stream", params={"target": "example.com"})
    assert response.status_code == 200
    assert "event: failure" in response.text
    assert "not_authorized" in response.text


def test_stream_reports_invalid_targets():
    response = client.get(
        "/api/v1/scans/stream", params={"target": "192.168.1.1", "authorized": "true"}
    )
    assert "event: failure" in response.text
    assert "invalid_target" in response.text


def test_scan_time_limit(monkeypatch):
    import asyncio

    async def slow_scan(target, on_event=None):
        await asyncio.sleep(5)

    monkeypatch.setattr(api, "scan", slow_scan)
    monkeypatch.setattr(api, "SCAN_TIME_LIMIT", 0.05)
    response = post()
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "timeout"
    assert api.slots.active == 0


def test_errors_are_translated():
    response = client.post(
        "/api/v1/scans", json={"target": "example.com", "authorized": False, "lang": "de"}
    )
    assert "bestätigen" in response.json()["detail"]["message"]


def test_stream_in_french():
    response = client.get(
        "/api/v1/scans/stream",
        params={"target": "example.com", "authorized": "true", "lang": "fr"},
    )
    assert "Connexion" in response.text


def test_unknown_language_is_rejected():
    response = client.get(
        "/api/v1/scans/stream", params={"target": "example.com", "authorized": "true", "lang": "xx"}
    )
    assert response.status_code == 422


def test_reports_are_signed_and_can_be_downloaded_as_pdf():
    report = post().json()
    assert report["signature"]
    response = client.post(
        "/api/v1/reports/pdf", json={"report": report, "lang": "fr", "platform": "nginx"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_a_forged_report_cannot_become_a_pdf():
    report = post().json()
    report["grade"] = "A+"
    response = client.post("/api/v1/reports/pdf", json={"report": report})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_report"


def test_oversized_requests_are_refused():
    response = client.post(
        "/api/v1/reports/pdf",
        content=b"{" + b" " * 1_100_000 + b"}",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413
