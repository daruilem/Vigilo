"""Markdown rendering of a report, for GitHub job summaries and pull request comments.

Observed values come from the scanned website, so they are never trusted as Markdown:
they are shown as inline code, with backticks and line breaks removed and length capped,
so a hostile header cannot inject links, images or HTML into the summary.
"""

from __future__ import annotations

import re

from vigilo.models import Finding, Platform, ScanReport, Severity, Status
from vigilo.pdf.labels import LABELS, PLATFORM_NAMES

SEVERITY_RANK = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}
UNGRADED_CHECKS = {"privacy"}
MAX_VALUE = 200


def code_span(value: str) -> str:
    """Untrusted text as a single-line inline code span."""
    text = re.sub(r"\s+", " ", value.replace("`", "'")).strip()
    if len(text) > MAX_VALUE:
        text = text[: MAX_VALUE - 1] + "…"
    return f"`{text}`" if text else "` `"


_MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]()!#|~>])")


def text(value: str) -> str:
    """A sentence as plain text: some embed values read from the site (versions, plugin
    names), so every Markdown character is escaped and HTML is neutralised."""
    flat = re.sub(r"\s+", " ", value).strip()
    return _MARKDOWN_SPECIAL.sub(r"\\\1", flat.replace("&", "&amp;").replace("<", "&lt;"))


def fence(code: str, info: str = "") -> str:
    longest = max((len(run) for run in re.findall(r"`+", code)), default=0)
    marks = "`" * max(3, longest + 1)
    return f"{marks}{info}\n{code.rstrip()}\n{marks}"


def _fix_for(finding: Finding, platform: Platform) -> tuple[Platform, str, str] | None:
    if not finding.fixes:
        return None
    chosen = platform if platform in finding.fixes else next(iter(finding.fixes))
    fix = finding.fixes[chosen]
    return chosen, fix.intro, fix.code


def render_markdown(
    report: ScanReport, language: str = "en", platform: Platform = Platform.APACHE
) -> str:
    labels = LABELS.get(language, LABELS["en"])
    issues = sorted(
        (f for f in report.findings if f.status in (Status.FAIL, Status.WARN)),
        key=lambda f: SEVERITY_RANK[f.severity],
    )
    passed = [f for f in report.findings if f.status in (Status.PASS, Status.INFO)]
    errors = [f for f in report.findings if f.status is Status.ERROR]

    out = [
        f"## {text(labels.title)}: {code_span(report.target)}",
        "",
        f"**{text(labels.grade)} {report.grade}** · {text(labels.your_score(report.score))}",
        "",
        text(labels.issues(len(issues))),
    ]

    if issues:
        out += ["", "| # | | |", "|---|---|---|"]
        for number, finding in enumerate(issues, 1):
            severity = labels.severity.get(finding.severity.value, "")
            out.append(f"| {number} | {severity} | {text(finding.headline or finding.title)} |")

    for number, finding in enumerate(issues, 1):
        severity = labels.severity.get(finding.severity.value, "")
        if finding.check in UNGRADED_CHECKS:
            severity = f"{severity} · {labels.not_graded}"
        out += [
            "",
            f"### {number}. {text(finding.headline or finding.title)}",
            "",
            f"**{severity}**",
        ]
        if finding.observed:
            out += ["", f"**{text(labels.observed)}**", ""]
            out += [f"- {text(o.label)}: {code_span(o.value)}" for o in finding.observed]
        out += ["", f"**{text(labels.why)}**", "", text(finding.description)]
        chosen = _fix_for(finding, platform)
        if chosen:
            fix_platform, intro, code = chosen
            out += [
                "",
                f"**{text(labels.fix(PLATFORM_NAMES[fix_platform.value]))}**",
                "",
                text(intro),
                "",
                fence(code),
            ]
        elif finding.recommendation:
            out += ["", f"**{text(labels.fix_fallback)}**", "", text(finding.recommendation)]
        if finding.follow_up:
            out += ["", f"{text(labels.then)} {text(finding.follow_up)}"]

    if not issues and not errors:
        out += ["", text(labels.all_clear)]

    if errors:
        out += [
            "",
            f"### {text(labels.not_checked(len(errors)))}",
            "",
            text(labels.not_checked_intro),
            "",
        ]
        out += [f"- {text(f.headline or f.title)}" for f in errors]

    if passed:
        out += ["", f"<details><summary>{text(labels.passed(len(passed)))}</summary>", ""]
        out += [f"- {text(f.headline or f.title)}" for f in passed]
        out += ["", "</details>"]

    return "\n".join(out) + "\n"
