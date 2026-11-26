from datetime import datetime, timedelta, timezone

import pytest

from vigilo.checks.tls import (
    CertificateInfo,
    evaluate_certificate,
    evaluate_protocols,
    parse_peer_certificate,
)
from vigilo.models import Severity, Status

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def cert(days_left: int) -> CertificateInfo:
    return CertificateInfo(
        subject="example.com",
        issuer="R11",
        not_before=NOW - timedelta(days=30),
        not_after=NOW + timedelta(days=days_left),
        san=["example.com", "www.example.com"],
    )


def expiry(days_left: int):
    return next(f for f in evaluate_certificate(cert(days_left), NOW) if f.id.endswith("expiry"))


@pytest.mark.parametrize(
    ("days", "status"),
    [
        (90, Status.PASS),
        (30, Status.PASS),
        (29, Status.WARN),
        (14, Status.WARN),
        (13, Status.FAIL),
        (0, Status.FAIL),
        (-5, Status.FAIL),
    ],
)
def test_certificate_expiry_thresholds(days, status):
    assert expiry(days).status is status


def test_expired_certificate_never_shows_negative_days():
    assert "expires in 0 days" in expiry(-5).description


def test_parse_peer_certificate():
    raw = {
        "subject": ((("commonName", "example.com"),),),
        "issuer": (
            (("countryName", "US"),),
            (("organizationName", "Let's Encrypt"),),
            (("commonName", "R11"),),
        ),
        "notBefore": "Jan  1 00:00:00 2026 GMT",
        "notAfter": "Apr  1 00:00:00 2026 GMT",
        "subjectAltName": (("DNS", "example.com"), ("DNS", "www.example.com")),
    }
    info = parse_peer_certificate(raw)
    assert info.subject == "example.com"
    assert info.issuer == "R11"
    assert info.not_after == datetime(2026, 4, 1, tzinfo=timezone.utc)
    assert info.san == ["example.com", "www.example.com"]


def protocols(**support):
    base = {"TLSv1.0": False, "TLSv1.1": False, "TLSv1.2": True, "TLSv1.3": True}
    base.update({k.replace("_", "."): v for k, v in support.items()})
    return {f.id: f for f in evaluate_protocols(base)}


def test_modern_configuration_passes():
    result = protocols()
    assert result["tls.legacy-protocols"].status is Status.PASS
    assert result["tls.modern-protocols"].status is Status.PASS


def test_legacy_protocols_fail():
    finding = protocols(TLSv1_0=True)["tls.legacy-protocols"]
    assert finding.status is Status.FAIL
    assert finding.severity is Severity.HIGH
    assert finding.evidence["accepted"] == ["TLSv1.0"]


def test_untestable_legacy_protocols_are_reported_honestly():
    finding = protocols(TLSv1_0=None, TLSv1_1=None)["tls.legacy-protocols"]
    assert finding.status is Status.INFO


def test_missing_tls13_is_a_warning():
    assert protocols(TLSv1_3=False)["tls.modern-protocols"].status is Status.WARN


def test_no_modern_protocol_is_critical():
    finding = protocols(TLSv1_2=False, TLSv1_3=False)["tls.modern-protocols"]
    assert finding.status is Status.FAIL
    assert finding.severity is Severity.CRITICAL


# --- a site without HTTPS ------------------------------------------------------------------


def _run_tls(monkeypatch, failure: Exception):
    import asyncio
    import ssl

    import httpx

    from vigilo import scoring
    from vigilo.checks import tls
    from vigilo.checks.base import ScanContext
    from vigilo.target import Target

    def refuse(host, port, address):
        raise failure

    monkeypatch.setattr(tls, "fetch_certificate", refuse)
    monkeypatch.setattr(tls, "probe_protocol", lambda *a: pytest.fail("no probe expected"))
    assert isinstance(ssl.SSLError(), OSError)  # why SSLError is re-raised first

    async def go():
        transport = httpx.MockTransport(lambda request: httpx.Response(200))
        async with httpx.AsyncClient(transport=transport) as http:
            ctx = ScanContext(target=Target("shop.example"), http=http)
            return await tls.TlsCheck().run(ctx)

    findings = asyncio.run(go())
    return findings, scoring.score(findings)


def test_site_without_https_fails_critically(monkeypatch):
    findings, score = _run_tls(monkeypatch, ConnectionRefusedError(111, "refused"))
    by_id = {f.id: f for f in findings}
    assert set(by_id) == {"tls.https", "tls.https-redirect"}
    assert by_id["tls.https"].status is Status.FAIL
    assert by_id["tls.https"].severity is Severity.CRITICAL
    assert by_id["tls.https-redirect"].status is Status.FAIL
    assert score == 50


def test_handshake_error_is_not_reported_as_missing_https(monkeypatch):
    import ssl

    with pytest.raises(ssl.SSLError):
        _run_tls(monkeypatch, ssl.SSLError(1, "handshake failure"))
