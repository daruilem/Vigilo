from vigilo.checks.privacy import evaluate
from vigilo.models import Status
from vigilo.scoring import score

CLEAN = """<html lang="en"><head><link rel="stylesheet" href="/style.css"></head>
<body><footer><a href="/privacy">Privacy policy</a></footer></body></html>"""


def by_id(findings):
    return {f.id: f for f in findings}


def test_clean_page_passes():
    results = by_id(evaluate(CLEAN, "shop.example"))
    assert results["privacy.google-fonts"].status is Status.PASS
    assert results["privacy.trackers"].status is Status.PASS
    assert results["legal.privacy-policy"].status is Status.PASS
    assert "legal.impressum" not in results  # not a German site


def test_google_fonts_are_reported():
    html = CLEAN.replace(
        "/style.css", "https://fonts.googleapis.com/css2?family=Roboto&display=swap"
    )
    finding = by_id(evaluate(html, "shop.example"))["privacy.google-fonts"]
    assert finding.status is Status.WARN
    assert finding.observed[0].value == "fonts.googleapis.com"


def test_trackers_without_consent_tool():
    html = CLEAN.replace(
        "</head>",
        '<script async src="https://www.googletagmanager.com/gtag/js?id=G-1"></script></head>',
    )
    finding = by_id(evaluate(html, "shop.example"))["privacy.trackers"]
    assert finding.status is Status.WARN
    assert "Google Tag Manager" in finding.observed[0].value


def test_trackers_with_consent_tool_are_a_note():
    html = CLEAN.replace(
        "</head>",
        '<script src="https://consent.cookiebot.com/uc.js"></script>'
        '<script src="https://connect.facebook.net/en_US/fbevents.js"></script></head>',
    )
    finding = by_id(evaluate(html, "shop.example"))["privacy.trackers"]
    assert finding.status is Status.INFO
    assert "Cookiebot" in finding.headline


def test_missing_privacy_link():
    html = "<html><body><a href='/contact'>Contact</a></body></html>"
    assert by_id(evaluate(html, "shop.example"))["legal.privacy-policy"].status is Status.WARN


def test_german_site_needs_an_impressum():
    html = '<html lang="de"><body><a href="/datenschutz">Datenschutz</a></body></html>'
    results = by_id(evaluate(html, "laden.example"))
    assert results["legal.impressum"].status is Status.FAIL
    assert results["legal.privacy-policy"].status is Status.PASS


def test_impressum_found_by_link_text():
    html = "<html><body><a href='/kontakt'>Impressum</a></body></html>"
    assert by_id(evaluate(html, "laden.de"))["legal.impressum"].status is Status.PASS


def test_french_site_needs_mentions_legales():
    html = '<html lang="fr"><body><a href="/mentions-legales">Mentions légales</a></body></html>'
    assert by_id(evaluate(html, "boutique.example"))["legal.mentions-legales"].status is Status.PASS
    html = '<html lang="fr"><body><a href="/contact">Contact</a></body></html>'
    assert by_id(evaluate(html, "boutique.example"))["legal.mentions-legales"].status is Status.FAIL


def test_legal_findings_do_not_change_the_security_grade():
    html = '<html lang="de"><body>nothing</body></html>'
    findings = evaluate(html, "laden.de")
    assert any(f.status is Status.FAIL for f in findings)
    assert score(findings) == 100
