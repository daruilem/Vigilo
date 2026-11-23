import pytest

from vigilo.models import Finding, Severity, Status
from vigilo.scoring import grade, score


def f(status: Status, severity: Severity = Severity.INFO) -> Finding:
    return Finding(id="x", check="x", title="x", status=status, severity=severity, description="")


def test_perfect_score():
    assert score([f(Status.PASS), f(Status.INFO)]) == 100


def test_failures_and_warnings_are_penalised():
    findings = [f(Status.FAIL, Severity.HIGH), f(Status.WARN, Severity.MEDIUM)]
    assert score(findings) == 100 - 20 - 5


def test_errors_do_not_change_the_score():
    assert score([f(Status.ERROR, Severity.CRITICAL)]) == 100


def test_score_never_goes_below_zero():
    assert score([f(Status.FAIL, Severity.CRITICAL)] * 5) == 0


@pytest.mark.parametrize(
    ("value", "letter"), [(100, "A"), (90, "A"), (89, "B"), (65, "C"), (50, "D"), (0, "F")]
)
def test_grades(value, letter):
    assert grade(value) == letter
