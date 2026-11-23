"""Privacy and legal basics, read from the home page HTML.

These findings concern data protection law rather than technical security, so they are
listed in the report but do not change the security grade (see scoring.UNSCORED_CHECKS).

Legal references:
- Google Fonts: LG München I, judgment of 20 January 2022, 3 O 17493/20 (GDPR).
- Consent before tracking: GDPR, ePrivacy Directive art. 5(3), § 25 TDDDG (Germany).
- Impressum: § 5 DDG (Germany), § 5 ECG (Austria).
- Mentions légales: art. 6 LCEN (France).
- Privacy notice: GDPR art. 13; Law 18-07 (Algeria).
"""

from __future__ import annotations

import re

from vigilo.checks.base import Check, ScanContext
from vigilo.htmlscan import PageInfo, read_page
from vigilo.models import Finding, Fix, Observation, Platform, Severity, Status

CHECK = "privacy"

GOOGLE_FONTS = ("fonts.googleapis.com", "fonts.gstatic.com")

TRACKERS: dict[str, str] = {
    "googletagmanager.com": "Google Tag Manager",
    "google-analytics.com": "Google Analytics",
    "connect.facebook.net": "Meta Pixel",
    "static.hotjar.com": "Hotjar",
    "snap.licdn.com": "LinkedIn Insight",
    "analytics.tiktok.com": "TikTok Pixel",
    "bat.bing.com": "Microsoft Advertising",
    "clarity.ms": "Microsoft Clarity",
    "mc.yandex.ru": "Yandex Metrica",
}

CONSENT_TOOLS: dict[str, str] = {
    "cookiebot": "Cookiebot",
    "onetrust": "OneTrust",
    "cookielaw.org": "OneTrust",
    "usercentrics": "Usercentrics",
    "borlabs": "Borlabs Cookie",
    "complianz": "Complianz",
    "cookieyes": "CookieYes",
    "iubenda": "iubenda",
    "didomi": "Didomi",
    "axeptio": "Axeptio",
    "tarteaucitron": "tarteaucitron",
    "klaro": "Klaro",
    "quantcast": "Quantcast Choice",
    "consentmanager": "consentmanager",
    "cookie-script.com": "Cookie Script",
}

PRIVACY_PATTERN = re.compile(
    r"privacy|datenschutz|confidentialit|donn[ée]es personnelles|protection des donn|"
    r"privacidad|privacy-policy|politique-de-confidentialite",
    re.IGNORECASE,
)
IMPRESSUM_PATTERN = re.compile(r"impressum|imprint|anbieterkennzeichnung", re.IGNORECASE)
MENTIONS_PATTERN = re.compile(r"mentions[\s-]*l[ée]gales|legal[\s-]*notice", re.IGNORECASE)


class PrivacyCheck(Check):
    name = CHECK
    label = "Privacy and legal basics (fonts, trackers, legal pages)"
    description = "Reads the home page for third-party fonts, trackers and legal links."

    async def run(self, ctx: ScanContext) -> list[Finding]:
        if not ctx.html:
            return [
                Finding(
                    id="privacy.unavailable",
                    check=CHECK,
                    title="Privacy and legal basics",
                    headline="The home page content could not be read",
                    status=Status.INFO,
                    description="The home page did not return HTML, so these points were skipped.",
                )
            ]
        return evaluate(ctx.html, ctx.target.hostname)


def found(html: str, needles: dict[str, str] | tuple[str, ...]) -> list[str]:
    lower = html.lower()
    if isinstance(needles, dict):
        return sorted({name for needle, name in needles.items() if needle in lower})
    return [n for n in needles if n in lower]


def has_link(page: PageInfo, pattern: re.Pattern[str]) -> bool:
    return any(pattern.search(link.text) or pattern.search(link.href) for link in page.links)


def is_german(page: PageInfo, hostname: str) -> bool:
    return page.lang.startswith("de") or hostname.endswith((".de", ".at"))


def is_french(page: PageInfo, hostname: str) -> bool:
    return page.lang.startswith("fr") or hostname.endswith(".fr")


def evaluate(html: str, hostname: str) -> list[Finding]:
    page = read_page(html)
    findings = [_google_fonts(html), _trackers(html), _privacy_policy(page)]
    if is_german(page, hostname):
        findings.append(_impressum(page))
    if is_french(page, hostname):
        findings.append(_mentions_legales(page))
    return findings


FONTS_FIXES = {
    Platform.APACHE: Fix(
        intro=(
            "Download the font files (for example with google-webfonts-helper), put them on "
            "your server, remove the Google <link> and declare them in your CSS:"
        ),
        code=(
            '@font-face {\n  font-family: "Your Font";\n'
            '  src: url("/fonts/your-font.woff2") format("woff2");\n  font-display: swap;\n}'
        ),
    ),
    Platform.CLOUDFLARE: Fix(
        intro=(
            "Speed, then Optimization, then Content Optimization. Turn on Cloudflare Fonts: "
            "Google Fonts are then served from your own domain."
        ),
        code="Cloudflare Fonts: On",
    ),
    Platform.WORDPRESS: Fix(
        intro=(
            "Use a plugin that hosts Google Fonts on your own site, such as OMGF, or your "
            "theme's local fonts option. Then check the page source again."
        ),
        code="Plugins > Add New > search: OMGF",
    ),
}
FONTS_FIXES[Platform.NGINX] = FONTS_FIXES[Platform.APACHE]

TRACKER_FIXES = {
    Platform.APACHE: Fix(
        intro=(
            "Load trackers only after the visitor agrees. With Google tags, start every page "
            "with consent denied, and grant it from your consent banner:"
        ),
        code=(
            "gtag('consent', 'default', {\n  ad_storage: 'denied',\n  ad_user_data: 'denied',\n"
            "  ad_personalization: 'denied',\n  analytics_storage: 'denied'\n});"
        ),
    ),
    Platform.CLOUDFLARE: Fix(
        intro="Cloudflare Zaraz can load third-party tools only after consent:",
        code="Zaraz > Consent > Enable consent management",
    ),
    Platform.WORDPRESS: Fix(
        intro=(
            "Install a consent plugin (for example Complianz, Borlabs Cookie or CookieYes) "
            "and let it block the trackers until the visitor agrees."
        ),
        code="Plugins > Add New > search: Complianz",
    ),
}
TRACKER_FIXES[Platform.NGINX] = TRACKER_FIXES[Platform.APACHE]


def _google_fonts(html: str) -> Finding:
    hosts = found(html, GOOGLE_FONTS)
    if hosts:
        return Finding(
            id="privacy.google-fonts", check=CHECK, title="Google Fonts",
            status=Status.WARN, severity=Severity.MEDIUM,
            description=(
                "Fonts are loaded from Google's servers, which receive every visitor's IP "
                "address without consent. A German court ruled this a GDPR violation and "
                "website owners have received warning letters for it."
            ),
            observed=[Observation(label="Loaded from", value=", ".join(hosts))],
            fixes=FONTS_FIXES,
            references=["LG München I, 20 January 2022, 3 O 17493/20"],
        )  # fmt: skip
    return Finding(
        id="privacy.google-fonts", check=CHECK, title="Google Fonts", status=Status.PASS,
        description="No fonts are loaded from Google's servers.",
    )  # fmt: skip


def _trackers(html: str) -> Finding:
    trackers = found(html, TRACKERS)
    consent = found(html, CONSENT_TOOLS)
    title = "Trackers and consent"
    if not trackers:
        return Finding(
            id="privacy.trackers", check=CHECK, title=title, status=Status.PASS,
            description="No common tracker is loaded by the home page HTML.",
        )  # fmt: skip
    observed = [Observation(label="Trackers in the page", value=", ".join(trackers))]
    if consent:
        observed.append(Observation(label="Consent tool", value=", ".join(consent)))
        return Finding(
            id="privacy.trackers", check=CHECK, title=title, status=Status.INFO,
            headline=f"Trackers found, with a consent tool ({consent[0]})",
            description=(
                "A consent tool is present. Check in your browser that trackers only start "
                "after the visitor clicks Accept."
            ),
            observed=observed,
        )  # fmt: skip
    return Finding(
        id="privacy.trackers", check=CHECK, title=title,
        status=Status.WARN, severity=Severity.MEDIUM,
        description=(
            "Tracking tools are loaded but no consent tool was found. In the EU, visitors "
            "must agree before such tools run."
        ),
        observed=observed, fixes=TRACKER_FIXES,
    )  # fmt: skip


def _privacy_policy(page: PageInfo) -> Finding:
    title = "Privacy policy link"
    if has_link(page, PRIVACY_PATTERN):
        return Finding(
            id="legal.privacy-policy", check=CHECK, title=title, status=Status.PASS,
            description="The home page links to a privacy policy.",
        )  # fmt: skip
    return Finding(
        id="legal.privacy-policy", check=CHECK, title=title,
        status=Status.WARN, severity=Severity.LOW,
        description=(
            "No link to a privacy policy was found on the home page. Visitors must be able "
            "to read how their data is used (GDPR art. 13, Algerian Law 18-07)."
        ),
        recommendation=(
            "Publish a privacy policy page and link it from the footer of every page."
        ),
    )  # fmt: skip


def _impressum(page: PageInfo) -> Finding:
    title = "Impressum"
    if has_link(page, IMPRESSUM_PATTERN):
        return Finding(
            id="legal.impressum", check=CHECK, title=title, status=Status.PASS,
            description="The home page links to an Impressum.",
        )  # fmt: skip
    return Finding(
        id="legal.impressum", check=CHECK, title=title,
        status=Status.FAIL, severity=Severity.MEDIUM,
        description=(
            "Business websites in Germany and Austria must link to an Impressum (§ 5 DDG, "
            "§ 5 ECG) that is easy to find. A missing one can lead to warning letters."
        ),
        recommendation=(
            "Create an Impressum page with your name, address and contact details, and link "
            "it from the footer of every page."
        ),
    )  # fmt: skip


def _mentions_legales(page: PageInfo) -> Finding:
    title = "Mentions légales"
    if has_link(page, MENTIONS_PATTERN):
        return Finding(
            id="legal.mentions-legales", check=CHECK, title=title, status=Status.PASS,
            description="The home page links to the legal notice (mentions légales).",
        )  # fmt: skip
    return Finding(
        id="legal.mentions-legales", check=CHECK, title=title,
        status=Status.FAIL, severity=Severity.MEDIUM,
        description=(
            "Websites published in France must show a legal notice (mentions légales, "
            "art. 6 LCEN) with the publisher's identity and the host's details."
        ),
        recommendation=(
            "Create a mentions légales page and link it from the footer of every page."
        ),
    )  # fmt: skip
