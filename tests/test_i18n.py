"""Every sentence a check can produce must exist in every catalog.

The scenarios below drive each check through all of its branches with pure functions,
then translate the findings. Any text left in English means a missing or mistyped
catalog entry.
"""

import asyncio
import re
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from vigilo import errors, guidance
from vigilo.active import jobs
from vigilo.checks import ALL_CHECKS, cms, email, files, headers, privacy, tls
from vigilo.checks.base import ScanContext
from vigilo.i18n import CATALOGS, localize_event, localize_finding, translate
from vigilo.models import Finding, Status
from vigilo.scanner import CONNECT_STEP
from vigilo.target import Target

LANGUAGES = sorted(CATALOGS)
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _redirect_findings() -> list[Finding]:
    def make(handler):
        async def go():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
                ctx = ScanContext(target=Target("shop.example"), http=http)
                return await tls._https_redirect(ctx)

        return asyncio.run(go())

    def redirects(request):
        if request.url.scheme == "http":
            return httpx.Response(301, headers={"Location": "https://shop.example/"})
        return httpx.Response(200)

    def refuses(request):
        raise httpx.ConnectError("refused", request=request)

    return [make(redirects), make(lambda r: httpx.Response(200)), make(refuses)]


def all_scenarios() -> list[Finding]:
    findings: list[Finding] = []

    # TLS
    for days in (5, 20, 90):
        cert = tls.CertificateInfo("x", "R11", NOW, NOW + timedelta(days=days), ["shop.example"])
        findings += tls.evaluate_certificate(cert, NOW)
    findings.append(tls._invalid_certificate("certificate has expired"))
    findings.append(tls.no_https("https://shop.example/"))
    for support in (
        {"TLSv1.0": True, "TLSv1.1": True, "TLSv1.2": True, "TLSv1.3": True},
        {"TLSv1.0": None, "TLSv1.1": None, "TLSv1.2": True, "TLSv1.3": False},
        {"TLSv1.0": False, "TLSv1.1": False, "TLSv1.2": False, "TLSv1.3": False},
    ):
        findings += tls.evaluate_protocols(support)
    findings += _redirect_findings()

    # Headers
    good = {
        "Strict-Transport-Security": "max-age=63072000",
        "Content-Security-Policy": "default-src 'self'; frame-ancestors 'self'",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "camera=()",
    }
    weak = {
        "Strict-Transport-Security": "max-age=60",
        "Content-Security-Policy": "script-src 'unsafe-inline'",
        "Referrer-Policy": "unsafe-url",
        "Server": "Apache/2.4.1",
    }
    findings += headers.evaluate_headers({}) + headers.evaluate_headers(good)
    findings += [*headers.evaluate_headers(weak), headers._unavailable()]

    # Files
    probe = files.Probe
    findings += files.evaluate_probes(
        [
            probe("/.git/HEAD", 200, 23, "text/plain"),
            probe("/.env", 200, None, "text/plain"),
            probe("/backup.zip", 200, 1000, "application/zip"),
        ]
    )
    findings += files.evaluate_probes([probe("/.env", 404, 0, "text/html")])

    # Email
    base = {"domain": "shop.example", "mx": ["aspmx.l.google.com"], "dkim_selectors": []}
    for spf, dmarc in (
        ([], []),
        (["v=spf1 -all", "v=spf1 ~all"], ["v=DMARC1; p=none"]),
        (["v=spf1 +all"], ["v=DMARC1; p=reject; pct=50"]),
        (["v=spf1 " + "include:a.example " * 11 + "-all"], ["v=DMARC1; p=reject"]),
        (["v=spf1 include:_spf.google.com"], ["v=DMARC1; p=quarantine"]),
        (["v=spf1 include:_spf.google.com -all"], []),
    ):
        findings += email.evaluate(email.EmailRecords(spf=spf, dmarc=dmarc, **base))
    findings += email.evaluate(
        email.EmailRecords(domain="x.example", mx=[], spf=[], dmarc=[], dkim_selectors=["k1"])
    )

    # CMS
    wp = cms.detect('<meta name="generator" content="WordPress 6.0.1">')
    findings += cms.evaluate(wp, "6.7.1") + cms.evaluate(wp, "6.0.1")
    findings += cms.evaluate(wp, None, {"contact-form-7": ("5.1", "5.9")})
    findings += cms.evaluate(wp, None, {"contact-form-7": ("5.9", "5.9")})
    findings += cms.evaluate(cms.detect('<script src="https://cdn.shopify.com/x.js">'))
    findings += cms.evaluate(cms.detect('<meta name="generator" content="Joomla! 4.2">'))

    # Privacy and legal
    findings += privacy.evaluate("<html lang='de'><body>x</body></html>", "laden.de")
    findings += privacy.evaluate("<html lang='fr'><body>x</body></html>", "boutique.fr")
    findings += privacy.evaluate(
        '<html lang="de"><link href="https://fonts.googleapis.com/css">'
        '<script src="https://www.googletagmanager.com/gtm.js"></script>'
        '<a href="/impressum">Impressum</a><a href="/datenschutz">Datenschutz</a></html>',
        "laden.de",
    )
    findings += privacy.evaluate(
        '<html lang="fr"><script src="https://consent.cookiebot.com/uc.js"></script>'
        '<script src="https://connect.facebook.net/x.js"></script>'
        '<a href="/mentions-legales">Mentions légales</a></html>',
        "boutique.fr",
    )

    # Errors reported by the scanner
    findings.append(
        Finding(
            id="tls.error",
            check="tls",
            title=tls.TlsCheck.label,
            headline=f"{tls.TlsCheck.label}: could not be checked",
            status=Status.ERROR,
            description="This check could not be completed, so its results are missing.",
        )
    )
    findings += [jobs._tool_error(tool) for tool in jobs.STEP_LABELS]
    return [guidance.enrich(f, "shop.example") for f in findings]


SCENARIOS = all_scenarios()

# Observation labels that are technical identifiers and stay as they are.
TECHNICAL = (
    "GET ",
    "TXT ",
    "TLSv1",
    "Strict-",
    "Content-",
    "X-",
    "Referrer-",
    "Permissions-",
    "Server",
)


def untranslated(finding: Finding, language: str) -> list[str]:
    translated = localize_finding(finding, language)
    missing = []
    for field in ("title", "headline", "description", "recommendation", "note", "follow_up"):
        before, after = getattr(finding, field), getattr(translated, field)
        if before and before == after and before not in KEEP_AS_IS:
            missing.append(f"{field}: {before}")
    for before, after in zip(finding.observed, translated.observed, strict=True):
        technical = (
            before.label.startswith(TECHNICAL)
            or before.label in KEEP_AS_IS
            or re.fullmatch(r"[a-z0-9-]+", before.label) is not None  # plugin slug
        )
        if not technical and before.label == after.label:
            missing.append(f"observed label: {before.label}")
    for platform, fix in finding.fixes.items():
        if fix.intro == translated.fixes[platform].intro:
            missing.append(f"fix intro: {fix.intro}")
    return missing


# Proper names and technical titles that are spelled the same in every language.
KEEP_AS_IS = {
    "Google Fonts",
    "Impressum",
    "Mentions légales",
    "Content Security Policy (CSP)",  # German keeps the English term
    "Generator",  # same word in German
    "HTTP Strict Transport Security (HSTS)",
}


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_finding_is_translated(language):
    missing = sorted({m for f in SCENARIOS for m in untranslated(f, language)})
    assert missing == []


@pytest.mark.parametrize("language", LANGUAGES)
def test_errors_and_steps_are_translated(language):
    messages = [
        errors.UNREACHABLE,
        errors.TIMEOUT,
        errors.TOO_MANY_REDIRECTS,
        errors.NOT_AUTHORIZED,
        errors.RATE_LIMITED,
        errors.TARGET_RATE_LIMITED,
        errors.BUSY,
        errors.SCAN_TIMEOUT,
        errors.INTERNAL,
        "The domain 'shop.example' does not exist. Check the spelling of the address.",
        "Enter a website address, for example example.com.",
        CONNECT_STEP["label"],
        *(check.label for check in ALL_CHECKS),
        errors.ACTIVE_DISABLED,
        errors.TERMS_NOT_ACCEPTED,
        errors.ACTIVE_RATE_LIMITED,
        errors.ACTIVE_TARGET_LIMITED,
        errors.ACTIVE_ALREADY_RUNNING,
        errors.ACTIVE_BUSY,
        errors.ACTIVE_NOT_FOUND,
        errors.ACTIVE_FAILED,
        jobs.PROOF_STEP["label"],
        jobs.ANALYSIS_STEP["label"],
        *jobs.STEP_LABELS.values(),
    ]
    assert [m for m in messages if translate(m, language) == m] == []


def test_catalogs_have_the_same_keys():
    keys = {language: set(catalog) for language, catalog in CATALOGS.items()}
    reference = keys["fr"]
    for language, language_keys in keys.items():
        assert language_keys == reference, language


def test_variable_parts_are_kept():
    text = "The certificate expires in 12 days."
    assert translate(text, "fr") == "Le certificat expire dans 12 jours."
    assert "12" in translate(text, "de")
    assert "12" in translate(text, "ar")


def test_plan_labels_are_translated():
    event = {"type": "plan", "steps": [CONNECT_STEP]}
    assert localize_event(event, "fr")["steps"][0]["label"] != CONNECT_STEP["label"]


def test_code_is_never_translated():
    finding = SCENARIOS[0]
    for fx in SCENARIOS:
        if fx.fixes:
            finding = fx
            break
    translated = localize_finding(finding, "de")
    for platform, fix in finding.fixes.items():
        assert translated.fixes[platform].code == fix.code


def test_unknown_language_returns_english():
    assert translate("not sent", "xx") == "not sent"


def test_no_template_repeats_a_placeholder():
    # Templates become regular expressions with one named group per placeholder.
    import re
    from collections import Counter

    for language, catalog in CATALOGS.items():
        for key in catalog:
            repeated = [n for n, c in Counter(re.findall(r"\{(\w+)\}", key)).items() if c > 1]
            assert not repeated, (language, key)
