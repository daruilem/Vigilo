"""Command-line interface: `vigilo scan example.com`."""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence

from rich.console import Console
from rich.table import Table

from vigilo import __version__
from vigilo.errors import ScanError
from vigilo.models import ScanReport, Status
from vigilo.scanner import scan

STATUS_STYLE = {
    Status.PASS: "[green]PASS[/]",
    Status.WARN: "[yellow]WARN[/]",
    Status.FAIL: "[red]FAIL[/]",
    Status.INFO: "[blue]INFO[/]",
    Status.ERROR: "[magenta]ERROR[/]",
}
GRADE_STYLE = {"A": "green", "B": "green", "C": "yellow", "D": "red", "F": "red"}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vigilo", description=__doc__)
    parser.add_argument("--version", action="version", version=f"vigilo {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="Run a passive security check-up of a website.")
    p_scan.add_argument("target", help="Domain or URL, e.g. example.com")
    p_scan.add_argument("--json", action="store_true", help="Print the report as JSON.")
    p_scan.add_argument(
        "--fail-under",
        type=int,
        metavar="SCORE",
        help="Exit with code 2 if the score is below SCORE (useful in CI pipelines).",
    )
    p_scan.add_argument(
        "--allow-private",
        action="store_true",
        help="Allow scanning hosts that resolve to private addresses (local testing only).",
    )

    args = parser.parse_args(argv)
    console = Console()

    try:
        report = asyncio.run(scan(args.target, allow_private=args.allow_private))
    except ScanError as exc:
        console.print(f"[red]Error:[/] {exc}")
        return 1

    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        render(report, console)

    if args.fail_under is not None and report.score < args.fail_under:
        return 2
    return 0


def render(report: ScanReport, console: Console) -> None:
    style = GRADE_STYLE.get(report.grade, "white")
    console.print(
        f"\n[bold]Vigilo report for {report.target}[/]  "
        f"score [bold {style}]{report.score}/100[/]  grade [bold {style}]{report.grade}[/]\n"
    )

    table = Table(show_lines=False)
    table.add_column("Status")
    table.add_column("Severity")
    table.add_column("Check")
    for f in report.findings:
        severity = f.severity.value if f.status in (Status.FAIL, Status.WARN) else ""
        table.add_row(STATUS_STYLE[f.status], severity, f.headline or f.title)
    console.print(table)

    to_fix = [f for f in report.findings if f.status in (Status.FAIL, Status.WARN)]
    if to_fix:
        console.print("\n[bold]What to fix[/]")
        for f in to_fix:
            console.print(f"\n[bold]- {f.title}[/]\n  {f.description}")
            if f.recommendation:
                console.print(f"  [cyan]Fix:[/] {f.recommendation}")


if __name__ == "__main__":
    sys.exit(main())
