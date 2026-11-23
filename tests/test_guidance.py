import pytest

from vigilo.guidance import FIXES, HEADLINES, enrich
from vigilo.models import Finding, Platform, Severity, Status


def finding(fid: str, status: Status) -> Finding:
    return Finding(
        id=fid, check="x", title="x", status=status, severity=Severity.MEDIUM, description=""
    )


@pytest.mark.parametrize("fid", sorted(FIXES))
def test_every_fix_covers_all_platforms(fid):
    assert set(FIXES[fid]) == set(Platform)
    for fix in FIXES[fid].values():
        assert fix.intro.strip() and fix.code.strip()


@pytest.mark.parametrize("fid", sorted(FIXES))
def test_every_fixable_finding_has_a_problem_headline(fid):
    assert Status.FAIL in HEADLINES[fid] or Status.WARN in HEADLINES[fid]


def test_enrich_failing_finding_gets_headline_fixes_and_domain():
    result = enrich(finding("tls.https-redirect", Status.FAIL), "shop.example")
    assert result.headline == "Visitors are not sent to the secure version of your site"
    assert set(result.fixes) == set(Platform)
    assert "server_name shop.example www.shop.example;" in result.fixes[Platform.NGINX].code
    assert "{domain}" not in result.fixes[Platform.NGINX].code


def test_enrich_passing_finding_gets_no_fixes():
    result = enrich(finding("headers.hsts", Status.PASS), "shop.example")
    assert result.headline == "Browsers are told to always use HTTPS"
    assert result.fixes == {}
    assert result.follow_up is None


def test_warning_falls_back_to_the_problem_headline():
    result = enrich(finding("headers.clickjacking", Status.WARN), "shop.example")
    assert result.headline == "Other sites can show your pages inside a hidden frame"


def test_follow_up_is_attached_to_problems():
    result = enrich(finding("files.env", Status.FAIL), "shop.example")
    assert result.follow_up is not None
