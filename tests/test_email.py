import asyncio

import pytest

from vigilo.checks.email import (
    UNKNOWN_INCLUDE,
    EmailRecords,
    count_spf_lookups,
    dmarc_tags,
    evaluate,
    mail_domain,
    provider_for,
    spf_all_qualifier,
    spf_lookup_count,
)
from vigilo.models import Platform, Severity, Status


def records(**kwargs):
    base = {
        "domain": "shop.example",
        "mx": ["aspmx.l.google.com"],
        "spf": ["v=spf1 include:_spf.google.com -all"],
        "dmarc": ["v=DMARC1; p=reject; rua=mailto:d@shop.example"],
        "dkim_selectors": ["google"],
    }
    base.update(kwargs)
    return EmailRecords(**base)


def by_id(findings):
    return {f.id: f for f in findings}


def test_mail_domain_drops_www():
    assert mail_domain("www.shop.example") == "shop.example"
    assert mail_domain("shop.example") == "shop.example"


@pytest.mark.parametrize(
    ("record", "qualifier"),
    [
        ("v=spf1 -all", "-"),
        ("v=spf1 include:x ~all", "~"),
        ("v=spf1 ?all", "?"),
        ("v=spf1 +all", "+"),
        ("v=spf1 all", "+"),
        ("v=spf1 include:x", None),
    ],
)
def test_spf_all_qualifier(record, qualifier):
    assert spf_all_qualifier(record) == qualifier


def test_spf_lookup_count():
    record = "v=spf1 ip4:1.2.3.4 include:a.example include:b.example mx a ~all"
    assert spf_lookup_count(record) == 4


def test_dmarc_tags():
    assert dmarc_tags("v=DMARC1; p=Quarantine; pct=50") == {
        "v": "dmarc1",
        "p": "quarantine",
        "pct": "50",
    }


def test_provider_from_mx():
    assert provider_for(["shop-example.mail.protection.outlook.com"]) == (
        "Microsoft 365",
        "include:spf.protection.outlook.com",
    )
    assert provider_for(["mx.unknown.example"]) is None


def test_well_configured_domain_passes():
    results = by_id(evaluate(records()))
    assert results["email.spf"].status is Status.PASS
    assert results["email.dmarc"].status is Status.PASS
    assert results["email.dkim"].status is Status.PASS


def test_missing_spf_suggests_a_record_for_the_detected_provider():
    spf = by_id(evaluate(records(spf=[])))["email.spf"]
    assert spf.status is Status.FAIL
    assert "include:_spf.google.com -all" in spf.fixes[Platform.CLOUDFLARE].code
    assert "Google Workspace" in spf.note


def test_missing_spf_without_mx_suggests_sending_nothing():
    spf = by_id(evaluate(records(spf=[], mx=[])))["email.spf"]
    assert 'v=spf1 -all"' in spf.fixes[Platform.APACHE].code


def test_unknown_provider_gets_a_placeholder():
    spf = by_id(evaluate(records(spf=[], mx=["mx.unknown.example"])))["email.spf"]
    assert UNKNOWN_INCLUDE in spf.fixes[Platform.APACHE].code


def test_plus_all_is_high_severity():
    spf = by_id(evaluate(records(spf=["v=spf1 +all"])))["email.spf"]
    assert spf.status is Status.FAIL
    assert spf.severity is Severity.HIGH
    assert "-all" in spf.fixes[Platform.APACHE].code


def test_two_spf_records_are_invalid():
    spf = by_id(evaluate(records(spf=["v=spf1 -all", "v=spf1 ~all"])))["email.spf"]
    assert spf.status is Status.FAIL
    assert len(spf.observed) == 2


def test_dmarc_monitoring_only_is_a_warning():
    dmarc = by_id(evaluate(records(dmarc=["v=DMARC1; p=none"])))["email.dmarc"]
    assert dmarc.status is Status.WARN
    assert "_dmarc.shop.example" in dmarc.fixes[Platform.APACHE].code


def test_missing_dmarc_fails():
    assert by_id(evaluate(records(dmarc=[])))["email.dmarc"].status is Status.FAIL


def test_missing_dkim_is_only_a_note():
    assert by_id(evaluate(records(dkim_selectors=[])))["email.dkim"].status is Status.INFO


def test_spf_lookups_follow_nested_includes():
    zone = {
        "a.example": ["v=spf1 include:b.example include:c.example -all"],
        "b.example": ["v=spf1 ip4:1.2.3.4 mx -all"],
        "c.example": ["v=spf1 include:a.example -all"],  # loops back
    }

    async def fake_txt(name):
        return zone.get(name, [])

    count = asyncio.run(count_spf_lookups("v=spf1 include:a.example a -all", fake_txt))
    # include:a, a, then inside a: include:b, include:c; inside b: mx; c: include:a (seen)
    assert count == 6


def test_nested_lookups_over_the_limit_fail():
    spf = by_id(evaluate(records(spf=["v=spf1 include:big.example -all"], spf_lookups=14)))[
        "email.spf"
    ]
    assert spf.status is Status.FAIL
    assert "14" in spf.description
