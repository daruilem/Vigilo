from datetime import datetime, timezone

import pytest
from test_pdf import sample_report

from vigilo import cli
from vigilo.i18n import localize_report
from vigilo.markdown import code_span, fence, render_markdown, text
from vigilo.models import Finding, Observation, Platform, ScanReport, Severity, Status

NOW = datetime(2026, 11, 26, 9, 0, tzinfo=timezone.utc)


def test_report_shows_grade_issue_and_fix_for_the_chosen_hosting():
    md = render_markdown(sample_report(), platform=Platform.NGINX)
    assert "**GRADE A**" in md
    assert "1 issue to fix" in md
    assert "HOW TO FIX IT \\(Nginx\\)" in md
    assert "add_header Strict-Transport-Security" in md
    assert "`not sent`" in md
    assert "<details><summary>1 check passed</summary>" in md


def test_falls_back_to_another_hosting_when_the_chosen_one_has_no_fix():
    report = sample_report()
    hsts = report.findings[0]
    hsts.fixes = {Platform.CLOUDFLARE: hsts.fixes[Platform.CLOUDFLARE]}
    md = render_markdown(report, platform=Platform.NGINX)
    assert "HOW TO FIX IT \\(Cloudflare\\)" in md


def test_report_is_translated_with_the_pdf_labels():
    md = render_markdown(localize_report(sample_report(), "de"), "de")
    assert "Sicherheits" in md
    assert "1 issue to fix" not in md


def test_clean_report_says_so():
    report = ScanReport(
        target="shop.example", started_at=NOW, finished_at=NOW, score=100, grade="A", findings=[]
    )
    assert "No problem was found" in render_markdown(report)


# --- values from the website cannot inject Markdown ---------------------------------------


def hostile_report() -> ScanReport:
    finding = Finding(
        id="headers.version",
        check="headers",
        title="Version disclosure",
        headline="Your server reveals [click](https://evil.example) ![x](https://evil.example/t.png)",
        status=Status.WARN,
        severity=Severity.LOW,
        description="<img src=https://evil.example/p.png> | broken | table",
        observed=[
            Observation(label="Server", value="nginx`\n\n# Injected\n![](https://evil.example)")
        ],
    )
    return ScanReport(
        target="shop.example",
        started_at=NOW,
        finished_at=NOW,
        score=98,
        grade="A",
        findings=[finding],
    )


def test_hostile_values_stay_inert():
    md = render_markdown(hostile_report())
    assert "[click](https" not in md
    assert "![x](" not in md
    assert "<img" not in md
    assert "\n# Injected" not in md
    # The table row keeps its three columns.
    row = next(line for line in md.splitlines() if line.startswith("| 1 |"))
    assert row.count(" | ") - row.count("\\|") == 2


def test_code_span_is_single_line_without_backticks_and_capped():
    span = code_span("a`b\nc" + "x" * 500)
    assert span.count("`") == 2
    assert "\n" not in span
    assert len(span) <= 202


def test_text_escapes_markdown():
    assert text("*bold* _it_ [a](b)") == "\\*bold\\* \\_it\\_ \\[a\\]\\(b\\)"


def test_fence_is_longer_than_any_backticks_in_the_code():
    assert fence("echo ````").startswith("`````\n")
    assert fence("plain").startswith("```\n")


# --- CLI ------------------------------------------------------------------------------------


@pytest.fixture
def fake_scan(monkeypatch):
    async def scan(target, allow_private=False):
        return sample_report()

    monkeypatch.setattr(cli, "scan", scan)


def test_cli_appends_markdown_and_honours_fail_under(fake_scan, tmp_path, capsys):
    summary = tmp_path / "summary.md"
    summary.write_text("previous step\n", encoding="utf-8")
    code = cli.main(
        ["scan", "shop.example", "--json", "--markdown", str(summary), "--fail-under", "95"]
    )
    assert code == 2
    content = summary.read_text(encoding="utf-8")
    assert content.startswith("previous step\n")
    assert "**GRADE A**" in content
    assert '"grade": "A"' in capsys.readouterr().out


def test_cli_translates_the_report(fake_scan, capsys):
    assert cli.main(["scan", "shop.example", "--json", "--lang", "fr"]) == 0
    out = capsys.readouterr().out
    assert "Browsers are not told" not in out
