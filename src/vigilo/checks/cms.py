"""CMS detection: which platform runs the site, whether it shows its version, whether
WordPress is up to date, and whether its plugins are.

Only the home page HTML and headers are used. Latest versions of WordPress and of its
plugins come from the public wordpress.org API and are cached for a few hours.
Plugin versions are read from the `?ver=` part of the plugin files linked by the page:
many plugins set it, some do not, so the plugin list can be incomplete.
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass

import httpx

from vigilo.checks.base import Check, ScanContext
from vigilo.htmlscan import read_page
from vigilo.models import Finding, Fix, Observation, Platform, Severity, Status

CHECK = "cms"
WORDPRESS_API = "https://api.wordpress.org/core/version-check/1.7/"
PLUGIN_API = "https://api.wordpress.org/plugins/info/1.2/"
CACHE_SECONDS = 6 * 3600
MAX_PLUGINS = 15
PLUGIN_ASSET = re.compile(
    r"/wp-content/plugins/([a-z0-9_-]+)/[^\"'\s?#<>]*\?(?:[^\"'\s#<>]*&(?:amp;)?)?ver=(\d+(?:\.\d+){1,3})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Cms:
    name: str
    hosted: bool  # updates handled by the platform itself
    markers: tuple[str, ...]


KNOWN: tuple[Cms, ...] = (
    Cms("WordPress", False, ("/wp-content/", "/wp-includes/", "wp-json")),
    Cms("Joomla", False, ("/media/jui/", "/media/system/js/", "joomla")),
    Cms("Drupal", False, ("drupal.settings", "/sites/default/files/", "drupal-settings-json")),
    Cms("PrestaShop", False, ("prestashop", "/modules/ps_")),
    Cms("Shopify", True, ("cdn.shopify.com", "shopify.theme")),
    Cms("Wix", True, ("static.wixstatic.com", "wix-bolt")),
    Cms("Squarespace", True, ("static1.squarespace.com", "squarespace-cdn")),
    Cms("Webflow", True, ("assets.website-files.com", "webflow.js")),
)

VERSION = re.compile(r"(\d+(?:\.\d+){1,2})")


@dataclass
class Detection:
    cms: Cms
    version: str | None
    source: str  # where the version or the platform was seen


_latest_wordpress: tuple[float, str] | None = None
_latest_plugins: dict[str, tuple[float, str | None]] = {}


class CmsCheck(Check):
    name = CHECK
    label = "Website platform (CMS) and updates"
    description = "Detects the CMS and checks whether WordPress is up to date."

    async def run(self, ctx: ScanContext) -> list[Finding]:
        headers = ctx.homepage.headers if ctx.homepage is not None else httpx.Headers()
        detection = detect(ctx.html, headers.get("x-generator", ""))
        if detection is None:
            return []
        latest = None
        plugins: dict[str, tuple[str, str | None]] = {}
        if detection.cms.name == "WordPress":
            if detection.version:
                latest = await latest_wordpress(ctx.http)
            installed = plugin_versions(ctx.html, detection.version)
            newest = await latest_plugin_versions(ctx.http, list(installed))
            plugins = {slug: (version, newest.get(slug)) for slug, version in installed.items()}
        return evaluate(detection, latest, plugins)


async def latest_wordpress(http: httpx.AsyncClient) -> str | None:
    global _latest_wordpress
    now = time.monotonic()
    if _latest_wordpress and now - _latest_wordpress[0] < CACHE_SECONDS:
        return _latest_wordpress[1]
    try:
        response = await http.get(WORDPRESS_API)
        current = str(response.json()["offers"][0]["current"])
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return None
    _latest_wordpress = (now, current)
    return current


async def latest_plugin_versions(http: httpx.AsyncClient, slugs: list[str]) -> dict[str, str]:
    """Latest version of each plugin on wordpress.org. Premium plugins are not listed there."""
    semaphore = asyncio.Semaphore(3)

    async def one(slug: str) -> tuple[str, str | None]:
        cached = _latest_plugins.get(slug)
        if cached and time.monotonic() - cached[0] < CACHE_SECONDS:
            return slug, cached[1]
        async with semaphore:
            try:
                response = await http.get(
                    PLUGIN_API, params={"action": "plugin_information", "request[slug]": slug}
                )
                data = response.json()
            except (httpx.HTTPError, ValueError):
                return slug, None
        version = str(data["version"]) if isinstance(data, dict) and "version" in data else None
        _latest_plugins[slug] = (time.monotonic(), version)
        return slug, version

    results = await asyncio.gather(*(one(s) for s in slugs[:MAX_PLUGINS]))
    return {slug: version for slug, version in results if version}


# --- pure logic (unit-tested) ---------------------------------------------------------


def plugin_versions(html: str, core_version: str | None = None) -> dict[str, str]:
    """Plugins linked by the page, with the version found in their `?ver=` parameter.

    A `ver` equal to the WordPress version is ignored: themes and WordPress itself often
    stamp files with the core version, which says nothing about the plugin.
    """
    found: dict[str, str] = {}
    for slug, version in PLUGIN_ASSET.findall(html):
        slug = slug.lower()
        if version == core_version or slug in found:
            continue
        found[slug] = version
    return found


def detect(html: str, generator_header: str = "") -> Detection | None:
    page = read_page(html) if html else None
    generator = (page.generator if page else "") or generator_header
    lower = html.lower()

    for cms in KNOWN:
        if generator.lower().startswith(cms.name.lower()):
            match = VERSION.search(generator)
            return Detection(cms, match.group(1) if match else None, f"generator: {generator}")
    for cms in KNOWN:
        if any(marker in lower for marker in cms.markers):
            return Detection(cms, None, "page resources")
    return None


def version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def is_outdated(version: str, latest: str) -> bool:
    current, newest = version_tuple(version), version_tuple(latest)
    width = max(len(current), len(newest))
    return current + (0,) * (width - len(current)) < newest + (0,) * (width - len(newest))


WP_HIDE_VERSION = {
    Platform.WORDPRESS: Fix(
        intro="Add this line to your child theme's functions.php, or use a security plugin option:",
        code="remove_action('wp_head', 'wp_generator');",
    ),
}

WP_UPDATE = {
    Platform.WORDPRESS: Fix(
        intro="Dashboard, then Updates, then Update now. Then turn on automatic updates:",
        code="Dashboard > Updates > Update to version {latest}",
    ),
    Platform.APACHE: Fix(
        intro="With command line access, WP-CLI updates WordPress, plugins and themes:",
        code="wp core update\nwp plugin update --all\nwp theme update --all",
    ),
}
WP_UPDATE[Platform.NGINX] = WP_UPDATE[Platform.APACHE]


def evaluate(
    detection: Detection,
    latest_wordpress: str | None = None,
    plugins: dict[str, tuple[str, str | None]] | None = None,
) -> list[Finding]:
    cms = detection.cms
    if cms.hosted:
        description = (
            f"{cms.name} installs security updates of the platform for you. Keep the apps "
            "and extensions you added up to date, and remove the ones you no longer use."
        )
    else:
        description = (
            f"{cms.name} must be updated by you or your host, together with its plugins and "
            "themes. Outdated plugins are the most common way small sites get hacked."
        )
    findings = [
        Finding(
            id="cms.detected",
            check=CHECK,
            title="Website platform",
            status=Status.INFO,
            headline=f"Built with {cms.name}",
            description=description,
            observed=[Observation(label="Detected from", value=detection.source)],
        )
    ]

    if detection.version and not cms.hosted:
        findings.append(
            Finding(
                id="cms.version-disclosed",
                check=CHECK,
                title="CMS version disclosure",
                status=Status.WARN,
                severity=Severity.LOW,
                headline=f"Your site shows its {cms.name} version",
                description=(
                    "The exact version helps attackers pick the known flaws to try first."
                ),
                observed=[Observation(label="Generator", value=f"{cms.name} {detection.version}")],
                fixes=WP_HIDE_VERSION if cms.name == "WordPress" else {},
                recommendation=f"Hide the generator tag in your {cms.name} settings or theme.",
            )
        )

    if cms.name == "WordPress" and detection.version and latest_wordpress:
        if is_outdated(detection.version, latest_wordpress):
            findings.append(
                Finding(
                    id="cms.wordpress-outdated",
                    check=CHECK,
                    title="WordPress updates",
                    status=Status.FAIL,
                    severity=Severity.HIGH,
                    headline=f"WordPress {detection.version} is out of date",
                    description=(
                        f"The latest version is {latest_wordpress}. Older versions have "
                        "published security flaws that attackers scan for automatically."
                    ),
                    observed=[
                        Observation(label="Installed", value=detection.version),
                        Observation(label="Latest", value=latest_wordpress),
                    ],
                    fixes={
                        p: Fix(intro=f.intro, code=f.code.replace("{latest}", latest_wordpress))
                        for p, f in WP_UPDATE.items()
                    },
                    follow_up="update every plugin and theme too, and delete the ones you do not use.",
                )
            )
        else:
            findings.append(
                Finding(
                    id="cms.wordpress-outdated",
                    check=CHECK,
                    title="WordPress updates",
                    status=Status.PASS,
                    headline="WordPress is up to date",
                    description=f"WordPress {detection.version} is the latest version.",
                    observed=[Observation(label="Installed", value=detection.version)],
                )
            )

    checked = {slug: v for slug, v in (plugins or {}).items() if v[1] is not None}
    if checked:
        findings.append(_plugins_finding(checked))
    return findings


PLUGIN_UPDATE = {
    Platform.WORDPRESS: Fix(
        intro="Dashboard, then Plugins. Select all plugins and choose Update in the bulk actions. Then turn on automatic updates:",
        code="Plugins > Installed Plugins > Bulk actions > Update",
    ),
    Platform.APACHE: Fix(
        intro="With command line access, WP-CLI updates WordPress, plugins and themes:",
        code="wp plugin update --all",
    ),
}
PLUGIN_UPDATE[Platform.NGINX] = PLUGIN_UPDATE[Platform.APACHE]
PLUGIN_NOTE = "Versions are read from the ?ver= part of the plugin files. Some plugins do not set it, so this list may be incomplete."


def _plugins_finding(plugins: dict[str, tuple[str, str | None]]) -> Finding:
    outdated = {
        slug: (installed, latest)
        for slug, (installed, latest) in sorted(plugins.items())
        if latest and is_outdated(installed, latest)
    }
    if outdated:
        return Finding(
            id="cms.plugins-outdated",
            check=CHECK,
            title="WordPress plugins",
            status=Status.FAIL,
            severity=Severity.HIGH,
            headline=f"Outdated WordPress plugins: {len(outdated)}",
            description="These plugins have newer versions on wordpress.org. Updates often fix security flaws that attackers scan for automatically.",
            observed=[
                Observation(label=slug, value=f"{installed} installed, {latest} available")
                for slug, (installed, latest) in outdated.items()
            ],
            note=PLUGIN_NOTE,
            fixes=PLUGIN_UPDATE,
            follow_up="delete the plugins you do not use: even deactivated plugins can be attacked.",
        )
    return Finding(
        id="cms.plugins-outdated",
        check=CHECK,
        title="WordPress plugins",
        status=Status.PASS,
        headline="Detected plugins are up to date",
        description=f"{len(plugins)} plugins were found and compared with wordpress.org.",
        observed=[Observation(label="Plugins checked", value=", ".join(sorted(plugins)))],
        note=PLUGIN_NOTE,
    )
