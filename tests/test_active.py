import json
from pathlib import Path

import pytest

from vigilo.active import ToolResult, parse_nuclei, parse_zap, to_findings
from vigilo.active.findings import (
    CATEGORIES,
    MAX_ADDRESSES,
    MAX_FINDINGS,
    NOT_SURE_NOTE,
    OTHER,
    categorize,
    to_finding,
)
from vigilo.active.parsers import Location
from vigilo.i18n import CATALOGS, localize_finding
from vigilo.models import Severity, Status

FIXTURES = Path(__file__).parent / "fixtures" / "active"
DOMAIN = "shop.example"
SECRETS = ("SECRET-DB-PASSWORD", "SECRET-SESSION-ID", "DB_PASSWORD", "<script>", "<form")


def nuclei():
    return parse_nuclei((FIXTURES / "nuclei.jsonl").read_text(encoding="utf-8"), DOMAIN)


def zap():
    return parse_zap((FIXTURES / "zap.json").read_text(encoding="utf-8"), DOMAIN)


def by_rule(results):
    return {r.rule: r for r in results}


# --- Nuclei ----------------------------------------------------------------------------


def test_nuclei_keeps_matches_on_the_verified_host_only():
    rules = by_rule(nuclei())
    assert "exposed-env" not in rules  # on cdn.other.example
    assert "unmatched" not in rules  # matcher-status false
    assert "truncated" not in rules  # broken last line is skipped, not fatal
    assert set(rules) == {
        "git-config",
        "CVE-2024-27956",
        "phpinfo-files",
        "cors-misconfig",
        "tech-detect",
        "phpmyadmin-panel",
    }


def test_nuclei_groups_addresses_per_template():
    cors = by_rule(nuclei())["cors-misconfig"]
    assert [loc.url for loc in cors.locations] == [
        "https://shop.example/api/cart",
        "https://shop.example/api/user",
    ]


def test_nuclei_reads_classification():
    cve = by_rule(nuclei())["CVE-2024-27956"]
    assert cve.severity is Severity.CRITICAL
    assert cve.cve == {"CVE-2024-27956"}
    assert cve.cwe == {89}
    assert cve.references == ["https://nvd.nist.gov/vuln/detail/CVE-2024-27956"]
    assert "sqli" in cve.tags


def test_nuclei_tags_as_a_comma_separated_string():
    assert by_rule(nuclei())["phpinfo-files"].tags == {"config", "exposure", "phpinfo"}


def test_garbage_input_gives_no_results():
    assert parse_nuclei("not json\n[1, 2]\n{}", DOMAIN) == []
    assert parse_zap("not json", DOMAIN) == []
    assert parse_zap('{"site": "nope"}', DOMAIN) == []


def match_line(url):
    return json.dumps({"template-id": "x", "info": {"severity": "high"}, "matched-at": url})


def test_subdomain_and_lookalike_hosts_are_out_of_scope():
    for url in (
        "https://www.shop.example/",
        "https://shop.example.evil.example/",
        "https://evil.example/?shop.example",
    ):
        assert parse_nuclei(match_line(url), DOMAIN) == []
    assert parse_nuclei(match_line("https://SHOP.example./a"), DOMAIN) != []


def test_very_long_addresses_are_cut():
    url = "https://shop.example/?q=" + "A" * 5000
    (result,) = parse_nuclei(match_line(url), DOMAIN)
    assert len(result.locations[0].url) <= 200


# --- ZAP -------------------------------------------------------------------------------


def test_zap_skips_false_positives_and_other_sites():
    rules = by_rule(zap())
    assert "40018" not in rules  # confidence 0: false positive
    assert set(rules) == {"10038", "40012", "10010", "10202", "10096"}
    assert all(
        loc.url.startswith("https://shop.example/") for r in rules.values() for loc in r.locations
    )


def test_zap_reads_risk_confidence_and_parameters():
    rules = by_rule(zap())
    assert rules["40012"].severity is Severity.HIGH
    assert rules["40012"].locations[0].parameter == "q"
    assert rules["10202"].uncertain
    assert not rules["40012"].uncertain
    assert rules["10096"].severity is Severity.INFO


# --- Findings --------------------------------------------------------------------------


def findings():
    return to_findings([*nuclei(), *zap()])


def test_findings_drop_info_and_what_the_passive_checks_already_report():
    ids = {f.id for f in findings()}
    assert ids == {
        "active.nuclei.cve-2024-27956",
        "active.nuclei.phpinfo-files",
        "active.nuclei.cors-misconfig",
        "active.zap.40012",
        "active.zap.10010",
        "active.zap.10202",
    }


def test_findings_are_sorted_worst_first():
    severities = [f.severity for f in findings()]
    order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
    assert severities == sorted(severities, key=order.index)
    assert findings()[0].id == "active.nuclei.cve-2024-27956"


def test_categories():
    expected = {
        "active.nuclei.cve-2024-27956": "known-vulnerability",
        "active.nuclei.phpinfo-files": "exposed-data",
        "active.nuclei.cors-misconfig": "misconfiguration",
        "active.zap.40012": "injection",
        "active.zap.10010": "cookies",
        "active.zap.10202": "misconfiguration",
    }
    assert {f.id: f.evidence["category"] for f in findings()} == expected


def test_unknown_results_fall_back_to_other():
    result = ToolResult(tool="zap", rule="1", name="Something new", severity=Severity.LOW)
    assert categorize(result) is OTHER


def test_no_site_data_ever_reaches_the_report():
    for finding in findings():
        text = finding.model_dump_json()
        for secret in SECRETS:
            assert secret not in text, (finding.id, secret)


def test_finding_content():
    xss = next(f for f in findings() if f.id == "active.zap.40012")
    assert xss.check == "active"
    assert xss.title == "Cross Site Scripting (Reflected)"
    assert xss.status is Status.FAIL
    assert [(o.label, o.value) for o in xss.observed] == [
        ("Found by", "OWASP ZAP (40012)"),
        ("Address", "https://shop.example/search?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E"),
        ("Parameter", "q"),
    ]

    cve = findings()[0]
    assert ("Known flaw", "CVE-2024-27956") in [(o.label, o.value) for o in cve.observed]
    assert "https://www.cve.org/CVERecord?id=CVE-2024-27956" in cve.references


def test_uncertain_results_are_warnings_with_a_note():
    csrf = next(f for f in findings() if f.id == "active.zap.10202")
    assert csrf.status is Status.WARN
    assert csrf.note == NOT_SURE_NOTE
    addresses = [o for o in csrf.observed if o.label == "Address"]
    assert len(addresses) == MAX_ADDRESSES
    assert ("Other affected addresses", "2") in [(o.label, o.value) for o in csrf.observed]


def test_same_cve_from_two_tools_is_reported_once():
    def result(tool):
        return ToolResult(
            tool=tool,
            rule="r",
            name="Flaw",
            severity=Severity.HIGH,
            cve=frozenset({"CVE-2024-1"}),
            locations=[Location("https://shop.example/a")],
        )

    assert len(to_findings([result("nuclei"), result("zap")])) == 1


def test_number_of_findings_is_capped():
    many = [
        ToolResult(
            tool="nuclei",
            rule=f"t{i}",
            name=f"Problem {i}",
            severity=Severity.MEDIUM,
            locations=[Location(f"https://shop.example/{i}")],
        )
        for i in range(MAX_FINDINGS + 10)
    ]
    assert len(to_findings(many)) == MAX_FINDINGS


# --- Translations ----------------------------------------------------------------------


SAME_IN_GERMAN = {"Parameter"}


@pytest.mark.parametrize("language", sorted(CATALOGS))
def test_active_findings_are_translated(language):
    samples = findings() + [to_finding_for(category) for category in (*CATEGORIES, OTHER)]
    missing = set()
    for finding in samples:
        translated = localize_finding(finding, language)
        for field in ("headline", "description", "recommendation", "note"):
            before = getattr(finding, field)
            if before and before == getattr(translated, field):
                missing.add(before)
        for before, after in zip(finding.observed, translated.observed, strict=True):
            if before.label == after.label and before.label not in SAME_IN_GERMAN:
                missing.add(before.label)
    assert sorted(missing) == []


def to_finding_for(category):
    # Every category's text, whatever results the fixtures happen to contain.
    result = ToolResult(
        tool="nuclei",
        rule="sample",
        name="Sample",
        severity=Severity.LOW,
        locations=[Location("https://shop.example/a", "p")],
        cve=frozenset({"CVE-2024-1"}),
        uncertain=True,
    )
    finding = to_finding(result)
    return finding.model_copy(
        update={
            "headline": category.headline,
            "description": category.description,
            "recommendation": category.recommendation,
        }
    )
