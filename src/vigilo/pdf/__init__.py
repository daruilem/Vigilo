"""PDF version of a report, in the printed inspection-report style of the web interface.

Arabic is written right to left: ReportLab does not do this alone, so Arabic paragraphs
are shaped (arabic-reshaper), wrapped into lines by measured width, and only then put in
visual order line by line (python-bidi). Doing it the other way round would show the
lines of a paragraph in the wrong order.

Latin runs inside Arabic text (versions, dates, header names) are wrapped in a
left-to-right embedding first, so they are never cut apart, and brackets are mirrored
by the Unicode bidi algorithm.
"""

from __future__ import annotations

import io
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from vigilo.models import Finding, Platform, ScanReport, Severity, Status
from vigilo.pdf.labels import DATE_FORMATS, LABELS, PLATFORM_NAMES, Labels

FONTS_DIR = Path(__file__).parent / "fonts"
FONT_FILES = {
    "Sans": "IBMPlexSansArabic-Regular.ttf",
    "Sans-SemiBold": "IBMPlexSansArabic-SemiBold.ttf",
    "Sans-Bold": "IBMPlexSansArabic-Bold.ttf",
    "Mono": "IBMPlexMono-Regular.ttf",
    "Mono-Medium": "IBMPlexMono-Medium.ttf",
    "Serif": "SourceSerif4-Semibold.ttf",
    "Serif-Bold": "SourceSerif4-Bold.ttf",
}

INK = colors.HexColor("#14181F")
MUTED = colors.HexColor("#5A606B")
RULE = colors.HexColor("#C9CCD1")
STAMP = colors.HexColor("#1F3A93")
HIGH = colors.HexColor("#B42318")
MEDIUM = colors.HexColor("#8A5300")
PASS = colors.HexColor("#1E6B45")

SEVERITY_RANK = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}
UNGRADED_CHECKS = {"privacy"}

PAGE_MARGIN = 18 * mm
_fonts_registered = False


def _register_fonts() -> None:
    global _fonts_registered
    if _fonts_registered:
        return
    for name, file in FONT_FILES.items():
        pdfmetrics.registerFont(TTFont(name, str(FONTS_DIR / file)))
    _fonts_registered = True


# --- text helpers ---------------------------------------------------------------------

_ARABIC = "؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿"
_LATIN_RUN = re.compile(rf"[^{_ARABIC}«»،؛]+")
_EDGE = " .,:;!?\"'·"
_CONTROLS = re.compile("[‪-‮⁦-⁩]")


def _embed_latin_runs(text: str) -> str:
    """Wrap each Latin run (with letters or digits) in a left-to-right embedding."""

    def wrap(match: re.Match[str]) -> str:
        run = match.group(0)
        core = run.strip(_EDGE)
        if not re.search(r"[A-Za-z0-9]", core):
            return run
        if core.startswith("(") and core.endswith(")") and core.count("(") == core.count(")"):
            core = core[1:-1]
        elif core.startswith("(") and core.count("(") > core.count(")"):
            core = core[1:]
        elif core.endswith(")") and core.count(")") > core.count("("):
            core = core[:-1]
        start = run.index(core)
        return run[:start] + "‪" + core + "‬" + run[start + len(core) :]

    return _LATIN_RUN.sub(wrap, text)


def _visual_rtl(line: str) -> str:
    return _CONTROLS.sub("", str(get_display(line, base_dir="R")))


class Writer:
    """Builds paragraphs in the reading direction of the report language."""

    def __init__(self, language: str, width: float) -> None:
        self.rtl = language == "ar"
        self.width = width

    def style(
        self, font: str, size: float, color: Any = INK, leading: float | None = None, **kw: Any
    ) -> ParagraphStyle:
        if self.rtl and font in ("Serif", "Serif-Bold", "Mono", "Mono-Medium"):
            # The serif and mono fonts have no Arabic letters.
            font = {
                "Serif": "Sans-Bold",
                "Serif-Bold": "Sans-Bold",
                "Mono": "Sans",
                "Mono-Medium": "Sans-SemiBold",
            }[font]
        return ParagraphStyle(
            name=f"{font}-{size}",
            fontName=font,
            fontSize=size,
            leading=leading or size * 1.4,
            textColor=color,
            alignment=TA_RIGHT if self.rtl else TA_LEFT,
            **kw,
        )

    def visual(self, text: str) -> str:
        """One line of text, in display order."""
        if not self.rtl:
            return text
        return _visual_rtl(arabic_reshaper.reshape(_embed_latin_runs(text)))

    def para(self, text: str, style: ParagraphStyle, width: float | None = None) -> Paragraph:
        if not self.rtl:
            return Paragraph(escape(text).replace("\n", "<br/>"), style)
        shaped = arabic_reshaper.reshape(_embed_latin_runs(text))
        lines = _wrap(shaped, style.fontName, style.fontSize, width or self.width)
        return Paragraph("<br/>".join(escape(_visual_rtl(line)) for line in lines), style)


def _wrap(text: str, font: str, size: float, width: float) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split(" "):
            candidate = f"{current} {word}" if current else word
            if current and pdfmetrics.stringWidth(_CONTROLS.sub("", candidate), font, size) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return lines


def code_block(code: str, width: float) -> Table:
    style = ParagraphStyle(
        name="code",
        fontName="Mono",
        fontSize=8,
        leading=11,
        textColor=INK,
        alignment=TA_LEFT,
        wordWrap="CJK",
    )
    markup = escape(code).replace("  ", "&nbsp; ").replace("\n", "<br/>")
    table = Table([[Paragraph(markup, style)]], colWidths=[width])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, RULE),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


# --- drawn elements ---------------------------------------------------------------------


class MarkLine(Flowable):
    """Section number, severity shape and label: the margin column of the web report."""

    def __init__(self, writer: Writer, number: str, kind: str, label: str, extra: str = "") -> None:
        super().__init__()
        self.writer, self.number, self.kind, self.label, self.extra = (
            writer,
            number,
            kind,
            label,
            extra,
        )
        self.height = 12

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        self.width = available_width
        return available_width, self.height

    def draw(self) -> None:
        c = self.canv
        color = {"critical": HIGH, "high": HIGH, "medium": MEDIUM, "low": MUTED, "pass": PASS}.get(
            self.kind, MUTED
        )
        rtl = self.writer.rtl
        parts: list[tuple[str, str, float, Any]] = [
            ("text", self.number, 0, INK),
            ("mark", "", 0, color),
        ]
        parts.append(("text", self.label, 0, color))
        if self.extra:
            parts.append(("text", f"· {self.extra}", 0, MUTED))

        x = self.width if rtl else 0.0
        for kind, text, _, col in parts:
            if kind == "mark":
                size = 7.0
                left = x - size if rtl else x
                self._shape(left, 1.5, size, col)
                step = size + 5
            else:
                font = "Mono" if text == self.number else "Sans-SemiBold"
                shown = self.writer.visual(text)
                width = pdfmetrics.stringWidth(shown, font, 8)
                c.setFillColor(col)
                c.setFont(font, 8)
                if rtl:
                    c.drawRightString(x, 2, shown)
                else:
                    c.drawString(x, 2, shown)
                step = width + 7
            x = x - step if rtl else x + step

    def _shape(self, x: float, y: float, size: float, color: Any) -> None:
        c = self.canv
        c.setStrokeColor(color)
        c.setFillColor(color)
        if self.kind in ("critical", "high"):
            c.rect(x, y, size, size, stroke=0, fill=1)
        elif self.kind == "medium":
            c.setLineWidth(1.4)
            c.rect(x + 0.7, y + 0.7, size - 1.4, size - 1.4, stroke=1, fill=0)
            c.rect(x, y, size / 2, size, stroke=0, fill=1)
        elif self.kind == "pass":
            c.setLineWidth(1.3)
            path = c.beginPath()
            path.moveTo(x + 0.5, y + size * 0.5)
            path.lineTo(x + size * 0.4, y + 0.8)
            path.lineTo(x + size, y + size)
            c.drawPath(path, stroke=1, fill=0)
        else:
            c.setLineWidth(0.8)
            c.rect(x + 0.4, y + 0.4, size - 0.8, size - 0.8, stroke=1, fill=0)


def grade_stamp(writer: Writer, grade: str, label: str) -> Table:
    inner = Table(
        [
            [writer.para(label, _center(writer, 7))],
            [
                Paragraph(
                    escape(grade),
                    ParagraphStyle(
                        name="stamp",
                        fontName="Serif-Bold",
                        fontSize=46,
                        leading=48,
                        textColor=STAMP,
                        alignment=1,
                    ),
                )
            ],
        ],
        colWidths=[78],
    )
    inner.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, STAMP),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    outer = Table([[inner]], colWidths=[86])
    outer.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1.8, STAMP),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return outer


def _center(writer: Writer, size: float) -> ParagraphStyle:
    style = writer.style("Sans-SemiBold", size, STAMP)
    style.alignment = 1
    return style


# --- report -----------------------------------------------------------------------------


def _choose_fix(finding: Finding, platform: Platform) -> tuple[Platform, Any] | None:
    if not finding.fixes:
        return None
    if platform in finding.fixes:
        return platform, finding.fixes[platform]
    first = next(iter(finding.fixes))
    return first, finding.fixes[first]


def _observed_table(writer: Writer, finding: Finding, value_color: Any) -> Table:
    label_style = writer.style("Mono", 8, MUTED, leading=11)
    value_style = writer.style(
        "Mono-Medium", 8, value_color, leading=11, wordWrap="CJK" if not writer.rtl else None
    )
    width = writer.width
    label_width, value_width = width * 0.38, width * 0.62
    rows = []
    for o in finding.observed:
        label = writer.para(o.label, label_style, label_width - 10)
        value = writer.para(o.value, value_style, value_width - 10)
        rows.append([value, label] if writer.rtl else [label, value])
    widths = [value_width, label_width] if writer.rtl else [label_width, value_width]
    table = Table(rows, colWidths=widths)
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _issue(
    writer: Writer, labels: Labels, finding: Finding, number: str, platform: Platform
) -> list[Flowable]:
    small_caps = writer.style("Sans-SemiBold", 7.5, INK, spaceBefore=8, spaceAfter=3)
    body = writer.style("Sans", 9.5, INK, leading=14)
    flow: list[Flowable] = [
        HRFlowable(width="100%", thickness=0.6, color=RULE, spaceBefore=6, spaceAfter=8),
        MarkLine(
            writer,
            number,
            finding.severity.value,
            labels.severity.get(finding.severity.value, ""),
            labels.not_graded if finding.check in UNGRADED_CHECKS else "",
        ),
        Spacer(1, 5),
        writer.para(finding.headline or finding.title, writer.style("Serif", 14, INK, leading=18)),
    ]
    if finding.headline:
        flow.append(writer.para(finding.title, writer.style("Mono", 8, MUTED, spaceBefore=1)))
    if finding.observed:
        flow += [writer.para(labels.observed, small_caps), _observed_table(writer, finding, HIGH)]
    # The heading stays with what it describes; the explanation and fix may continue on the
    # next page instead of leaving half a page empty.
    head, flow = flow, []
    if finding.note:
        flow.append(writer.para(finding.note, writer.style("Sans", 8, MUTED, spaceBefore=3)))
    flow += [writer.para(labels.why, small_caps), writer.para(finding.description, body)]

    chosen = _choose_fix(finding, platform)
    if chosen:
        chosen_platform, fix = chosen
        flow += [
            writer.para(labels.fix(PLATFORM_NAMES[chosen_platform.value]), small_caps),
            writer.para(fix.intro, writer.style("Sans", 9, INK, leading=13, spaceAfter=4)),
            code_block(fix.code, writer.width),
        ]
    elif finding.recommendation:
        flow += [
            writer.para(labels.fix_fallback, small_caps),
            writer.para(finding.recommendation, body),
        ]
    if finding.follow_up:
        flow.append(
            writer.para(
                f"{labels.then} {finding.follow_up}",
                writer.style("Sans", 9, INK, leading=13, spaceBefore=5),
            )
        )
    return [KeepTogether(head), *flow]


def _summary_list(writer: Writer, findings: Sequence[Finding], color: Any) -> Table:
    left, right = writer.width * 0.45, writer.width * 0.55
    title_style = writer.style("Sans", 9, INK, leading=12)
    value_style = writer.style(
        "Mono", 7.5, color, leading=10, wordWrap="CJK" if not writer.rtl else None
    )
    rows = []
    for f in findings:
        title = writer.para(f.headline or f.title, title_style, left - 8)
        value = writer.para(
            " · ".join(f"{o.label}: {o.value}" for o in f.observed), value_style, right - 8
        )
        rows.append([value, title] if writer.rtl else [title, value])
    table = Table(rows, colWidths=[right, left] if writer.rtl else [left, right])
    table.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, 0), 0.9, INK),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def render_report(
    report: ScanReport, language: str = "en", platform: Platform = Platform.APACHE
) -> bytes:
    """Render a (translated) report as PDF bytes."""
    _register_fonts()
    labels = LABELS.get(language, LABELS["en"])
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN + 6 * mm,
        bottomMargin=PAGE_MARGIN,
        title=f"Vigilo · {report.target}",
        author="Vigilo",
        subject=labels.title,
    )
    writer = Writer(language, doc.width)

    issues = sorted(
        (f for f in report.findings if f.status in (Status.FAIL, Status.WARN)),
        key=lambda f: SEVERITY_RANK[f.severity],
    )
    passed = [f for f in report.findings if f.status in (Status.PASS, Status.INFO)]
    errors = [f for f in report.findings if f.status is Status.ERROR]

    # Header: title, address, date, grade stamp.
    counts = [
        f"{sum(1 for f in issues if f.severity is s)} {labels.severity[s.value].lower()}"
        for s in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW)
        if any(f.severity is s for f in issues)
    ]
    meta = writer.style("Sans", 8.5, MUTED, leading=12)
    left_width = doc.width - 100
    left: list[Flowable] = [
        writer.para(labels.title, writer.style("Serif-Bold", 24, INK, leading=28), left_width),
        Paragraph(
            escape(f"https://{report.target}/"),
            ParagraphStyle(
                name="url",
                fontName="Mono",
                fontSize=11,
                leading=16,
                textColor=INK,
                alignment=TA_RIGHT if writer.rtl else TA_LEFT,
                spaceBefore=4,
                spaceAfter=8,
            ),
        ),
        writer.para(
            f"{labels.checked_on}: {report.finished_at.strftime(DATE_FORMATS.get(language, DATE_FORMATS['en']))}",
            meta,
            left_width,
        ),
        writer.para(f"{labels.method}: {labels.method_value}", meta, left_width),
        writer.para(f"{labels.hosting}: {PLATFORM_NAMES[platform.value]}", meta, left_width),
        Spacer(1, 8),
        writer.para(labels.issues(len(issues)), writer.style("Sans-SemiBold", 11, INK), left_width),
    ]
    if counts:
        left.append(writer.para(" · ".join(counts), meta, left_width))
    stamp = grade_stamp(writer, report.grade, labels.grade)
    header = Table(
        [[stamp, left]] if writer.rtl else [[left, stamp]],
        colWidths=[100, left_width] if writer.rtl else [left_width, 100],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story: list[Flowable] = [header, Spacer(1, 6)]
    for index, finding in enumerate(issues):
        story.extend(_issue(writer, labels, finding, f"{index + 1:02d}", platform))
    if not issues:
        story += [
            HRFlowable(width="100%", thickness=0.6, color=RULE, spaceBefore=6, spaceAfter=8),
            writer.para(labels.all_clear, writer.style("Sans", 10, PASS)),
        ]

    if errors:
        story += [
            HRFlowable(width="100%", thickness=0.6, color=RULE, spaceBefore=10, spaceAfter=8),
            writer.para(
                labels.not_checked(len(errors)), writer.style("Serif", 13, INK, leading=17)
            ),
            writer.para(labels.not_checked_intro, writer.style("Sans", 9, MUTED, spaceAfter=4)),
            _summary_list(writer, errors, MUTED),
        ]
    if passed:
        story += [
            HRFlowable(width="100%", thickness=0.6, color=RULE, spaceBefore=10, spaceAfter=8),
            KeepTogether(
                [
                    MarkLine(
                        writer,
                        f"{len(issues) + (1 if errors else 0) + 1:02d}",
                        "pass",
                        labels.severity["pass"],
                    ),
                    Spacer(1, 5),
                    writer.para(
                        labels.passed(len(passed)),
                        writer.style("Serif", 13, INK, leading=17, spaceAfter=6),
                    ),
                    _summary_list(writer, passed, PASS),
                ]
            ),
        ]

    def decorate(canvas: Any, document: Any) -> None:
        canvas.saveState()
        width, height = A4
        canvas.setStrokeColor(INK)
        canvas.setLineWidth(1.2)
        canvas.line(
            PAGE_MARGIN, height - PAGE_MARGIN + 2, width - PAGE_MARGIN, height - PAGE_MARGIN + 2
        )
        canvas.setFont("Serif-Bold", 11)
        canvas.setFillColor(INK)
        canvas.drawString(PAGE_MARGIN, height - PAGE_MARGIN + 6, "Vigilo")
        canvas.setFont("Mono", 8)
        canvas.drawRightString(width - PAGE_MARGIN, height - PAGE_MARGIN + 6, report.target)
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.6)
        canvas.line(PAGE_MARGIN, PAGE_MARGIN - 6, width - PAGE_MARGIN, PAGE_MARGIN - 6)
        canvas.setFont("Sans", 7.5)
        canvas.setFillColor(MUTED)
        footer, page = writer.visual(labels.footer), writer.visual(labels.page(document.page))
        if writer.rtl:
            canvas.drawRightString(width - PAGE_MARGIN, PAGE_MARGIN - 16, footer)
            canvas.drawString(PAGE_MARGIN, PAGE_MARGIN - 16, page)
        else:
            canvas.drawString(PAGE_MARGIN, PAGE_MARGIN - 16, footer)
            canvas.drawRightString(width - PAGE_MARGIN, PAGE_MARGIN - 16, page)
        canvas.restoreState()

    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    return buffer.getvalue()


def file_name(report: ScanReport) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ".-" else "-" for ch in report.target)
    return f"vigilo-{safe}-{report.finished_at:%Y-%m-%d}.pdf"
