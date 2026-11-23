"""Turn findings into a 0-100 score and a letter grade."""

from __future__ import annotations

from collections.abc import Iterable

from vigilo.models import Finding, Severity, Status

PENALTIES: dict[Severity, int] = {
    Severity.CRITICAL: 40,
    Severity.HIGH: 20,
    Severity.MEDIUM: 10,
    Severity.LOW: 3,
    Severity.INFO: 0,
}

# Legal and privacy findings are reported but do not change the security grade.
UNSCORED_CHECKS = frozenset({"privacy"})

GRADES: list[tuple[int, str]] = [(90, "A"), (80, "B"), (65, "C"), (50, "D"), (0, "F")]


def penalty(finding: Finding) -> int:
    if finding.check in UNSCORED_CHECKS:
        return 0
    base = PENALTIES[finding.severity]
    if finding.status is Status.FAIL:
        return base
    if finding.status is Status.WARN:
        return base // 2
    return 0


def score(findings: Iterable[Finding]) -> int:
    return max(0, 100 - sum(penalty(f) for f in findings))


def grade(value: int) -> str:
    return next(letter for threshold, letter in GRADES if value >= threshold)
