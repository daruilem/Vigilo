import json
from datetime import datetime, timezone

import pytest

from vigilo import guidance
from vigilo.i18n import localize_report
from vigilo.models import Finding, Observation, Platform, ScanReport, Severity, Status
from vigilo.pdf import _embed_latin_runs, _visual_rtl, file_name, render_report
from vigilo.signing import sign, verify

NOW = datetime(2026, 11, 23, 20, 0, tzinfo=timezone.utc)


def sample_report() -> ScanReport:
    findings = [
        guidance.enrich(
            Finding(
                id="headers.hsts",
                check="headers",
                title="HTTP Strict Transport Security (HSTS)",
                status=Status.FAIL,
                severity=Severity.MEDIUM,
                description=(
                    "Browsers are not told to always use a secure connection. A visitor on a "
                    "public Wi-Fi can be silently downgraded to an unencrypted connection."
                ),
                observed=[Observation(label="Strict-Transport-Security", value="not sent")],
            ),
            "shop.example",
        ),
        guidance.enrich(
            Finding(
                id="tls.modern-protocols",
                check="tls",
                title="Modern TLS versions",
                status=Status.PASS,
                description="The server supports TLS 1.3.",
                observed=[Observation(label="TLSv1.3", value="accepted")],
            ),
            "shop.example",
        ),
    ]
    return ScanReport(
        target="shop.example",
        started_at=NOW,
        finished_at=NOW,
        score=90,
        grade="A",
        findings=findings,
    )


# --- signatures ----------------------------------------------------------------------------


def test_signed_report_verifies_after_a_json_round_trip():
    signed = sign(sample_report())
    again = ScanReport.model_validate(json.loads(signed.model_dump_json()))
    assert verify(again)


def test_edited_report_is_refused():
    signed = sign(sample_report())
    forged = signed.model_copy(update={"grade": "A+", "score": 100})
    assert not verify(forged)


def test_unsigned_report_is_refused():
    assert not verify(sample_report())


# --- rendering -----------------------------------------------------------------------------


@pytest.mark.parametrize("language", ["en", "fr", "de", "ar"])
def test_renders_a_pdf_in_every_language(language):
    data = render_report(localize_report(sample_report(), language), language, Platform.NGINX)
    assert data.startswith(b"%PDF")
    assert len(data) > 5_000


def test_file_name_is_safe():
    report = sample_report().model_copy(update={"target": 'evil"name/../x'})
    assert file_name(report) == "vigilo-evil-name-..-x-2026-11-23.pdf"


@pytest.mark.parametrize(
    ("logical", "expected_inside"),
    [
        ("طريقة الإصلاح (Nginx)", "(Nginx)"),
        ("أرسل «camera=(), microphone=()» الآن.", "camera=(), microphone=()"),
        ("تاريخ الفحص: 2026-11-23, 22:01 UTC", "2026-11-23, 22:01 UTC"),
    ],
)
def test_latin_runs_stay_intact_in_arabic(logical, expected_inside):
    assert expected_inside in _visual_rtl(_embed_latin_runs(logical))


@pytest.mark.parametrize("language", ["en", "fr", "de", "ar"])
def test_active_scan_reports_render_with_their_own_labels(language):
    from vigilo.pdf.labels import LABELS

    active = sample_report().model_copy(update={"kind": "active"})
    assert render_report(localize_report(active, language), language).startswith(b"%PDF")
    labels = LABELS[language]
    assert labels.title_active != labels.title
    assert labels.footer_active != labels.footer


def test_active_scan_pdf_file_name():
    active = sample_report().model_copy(update={"kind": "active"})
    assert file_name(active) == "vigilo-active-shop.example-2026-11-23.pdf"
    assert file_name(sample_report()) == "vigilo-shop.example-2026-11-23.pdf"
