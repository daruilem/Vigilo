"""Turn tool results into report findings a non-expert can act on.

Scanners know thousands of problems, each with its own English name. Translating each
one is impossible, and their wording is written for security experts anyway. So every
result is sorted into a small set of categories, each with its own plain-language
headline, explanation and advice, translated like the rest of the report. The tool's
own name for the problem is kept as the technical title, shown as-is.

Results already covered by the passive check-up (security headers, TLS, the sensitive
files it probes) are dropped, so one problem is never counted twice.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from urllib.parse import urlsplit

from vigilo.active.parsers import ToolResult
from vigilo.checks.files import GROUPS
from vigilo.models import Finding, Observation, Severity, Status

CHECK = "active"
MAX_FINDINGS = 40
MAX_ADDRESSES = 5
TOOL_NAMES = {"nuclei": "Nuclei", "zap": "OWASP ZAP"}
SEVERITY_ORDER = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]

# Already reported by the passive checks.
PASSIVE_ZAP_RULES = frozenset(
    {
        "10020",  # anti-clickjacking header
        "10021",  # X-Content-Type-Options
        "10035",  # Strict-Transport-Security
        "10036",  # server version in the Server header
        "10037",  # X-Powered-By
        "10038",  # Content-Security-Policy missing
        "10055",  # Content-Security-Policy weaknesses
        "10063",  # Permissions-Policy
    }
)
PASSIVE_NUCLEI_TEMPLATES = frozenset(
    {
        "http-missing-security-headers",
        "tls-version",
        "deprecated-tls",
        "expired-ssl",
        "self-signed-ssl",
        "mismatched-ssl-certificate",
        "ssl-dns-names",
        "ssl-issuer",
        "tech-detect",
        "waf-detect",
    }
)
PASSIVE_PATHS = frozenset(path for group in GROUPS for path in group.paths)

NOT_SURE_NOTE = (
    "The scanner is not sure about this result. Check it by hand before changing anything."
)


@dataclass(frozen=True)
class Category:
    id: str
    headline: str
    description: str
    recommendation: str
    matches: Callable[[ToolResult], bool]


def _tags(*names: str) -> Callable[[ToolResult], bool]:
    wanted = frozenset(names)
    return lambda r: bool(r.tags & wanted)


def _cwe(*ids: int) -> Callable[[ToolResult], bool]:
    wanted = frozenset(ids)
    return lambda r: bool(r.cwe & wanted)


def _any(*tests: Callable[[ToolResult], bool]) -> Callable[[ToolResult], bool]:
    return lambda r: any(test(r) for test in tests)


# Checked in this order: the first matching category wins.
CATEGORIES: tuple[Category, ...] = (
    Category(
        id="known-vulnerability",
        headline="Software on your site has a known security flaw",
        description=(
            "This software version has a publicly documented flaw. Attackers use automated "
            "tools that search the internet for exactly these flaws."
        ),
        recommendation=(
            "Update the software named below to its latest version. If you cannot, ask "
            "your web developer or host to do it as soon as possible."
        ),
        matches=lambda r: bool(r.cve) or "cve" in r.tags,
    ),
    Category(
        id="injection",
        headline="Your site accepts dangerous input",
        description=(
            "The scanner could make your site run or show content that it sent. Attackers "
            "use this to steal visitor sessions, read the database or take over the server."
        ),
        recommendation=(
            "Ask your web developer to check and escape every input at the addresses "
            "below. If the site uses a CMS, update it and its plugins first: the flaw is "
            "often in an old plugin."
        ),
        matches=_any(
            _tags("xss", "sqli", "rce", "lfi", "rfi", "ssti", "injection", "cmdi", "xxe", "ssrf"),
            _cwe(77, 78, 79, 89, 22, 23, 94, 98, 611, 918, 1336),
        ),
    ),
    Category(
        id="cookies",
        headline="Your cookies are missing protection flags",
        description=(
            "Without the Secure, HttpOnly and SameSite flags, a session cookie can be "
            "stolen on public Wi-Fi or by a malicious script. The attacker can then log in "
            "as your visitor."
        ),
        recommendation=(
            "Set the Secure, HttpOnly and SameSite flags on the cookies at the addresses "
            "below. In most CMS this is a setting or a small plugin; otherwise ask your "
            "developer."
        ),
        matches=_cwe(614, 1004, 1275),
    ),
    Category(
        id="admin-panel",
        headline="An administration page is open to the internet",
        description=(
            "Admin and login pages are the first target of password-guessing attacks, "
            "which run day and night against every site they find."
        ),
        recommendation=(
            "Limit access to this page (by IP address, an extra password or a VPN) and "
            "turn on two-factor authentication for every account."
        ),
        matches=_tags("panel", "login"),
    ),
    Category(
        id="exposed-data",
        headline="Private files or information can be read",
        description=(
            "Configuration files, logs or folder listings can reveal passwords, internal "
            "addresses or customer data to anyone who finds them."
        ),
        recommendation=(
            "Delete these files from the public folder, or block access to them in your "
            "server settings. Then change any password they may contain."
        ),
        matches=_any(
            _tags("exposure", "config", "backup", "logs", "disclosure", "files", "listing"),
            _cwe(200, 215, 497, 530, 532, 538, 548),
        ),
    ),
    Category(
        id="misconfiguration",
        headline="A server setting weakens your protection",
        description=(
            "The server accepts settings or requests that attackers can misuse, for "
            "example sharing visitor data with any other website."
        ),
        recommendation=(
            "Review the setting named below with your host or developer, and use the "
            "strictest value that still lets the site work."
        ),
        matches=_any(_tags("misconfig", "misconfiguration", "cors"), _cwe(16, 352, 942, 1021)),
    ),
)
OTHER = Category(
    id="other",
    headline="The active scan found a possible problem",
    description=(
        "The scanner found something that may weaken your site. The technical name above "
        "describes it."
    ),
    recommendation="Show this result to your web developer or host and ask them to check it.",
    matches=lambda r: True,
)


def categorize(result: ToolResult) -> Category:
    return next((c for c in CATEGORIES if c.matches(result)), OTHER)


def covered_by_passive_checks(result: ToolResult) -> bool:
    if result.tool == "zap" and result.rule in PASSIVE_ZAP_RULES:
        return True
    if result.tool == "nuclei" and result.rule in PASSIVE_NUCLEI_TEMPLATES:
        return True
    paths = {urlsplit(loc.url).path for loc in result.locations}
    return bool(paths) and paths <= PASSIVE_PATHS


def _slug(rule: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", rule.lower()).strip("-") or "unknown"


def to_finding(result: ToolResult) -> Finding:
    category = categorize(result)
    tool = TOOL_NAMES.get(result.tool, result.tool)
    observed = [Observation(label="Found by", value=f"{tool} ({result.rule})")]
    if result.cve:
        observed.append(Observation(label="Known flaw", value=", ".join(sorted(result.cve))))
    for location in result.locations[:MAX_ADDRESSES]:
        observed.append(Observation(label="Address", value=location.url))
        if location.parameter:
            observed.append(Observation(label="Parameter", value=location.parameter))
    hidden = len(result.locations) - MAX_ADDRESSES
    if hidden > 0:
        observed.append(Observation(label="Other affected addresses", value=str(hidden)))

    references = list(result.references)
    references += [f"https://www.cve.org/CVERecord?id={cve}" for cve in sorted(result.cve)]
    return Finding(
        id=f"{CHECK}.{result.tool}.{_slug(result.rule)}",
        check=CHECK,
        title=result.name,
        headline=category.headline,
        status=Status.WARN if result.uncertain else Status.FAIL,
        severity=result.severity,
        description=category.description,
        recommendation=category.recommendation,
        observed=observed,
        note=NOT_SURE_NOTE if result.uncertain else None,
        references=references,
        evidence={
            "tool": result.tool,
            "rule": result.rule,
            "category": category.id,
            "cwe": sorted(result.cwe),
            "cve": sorted(result.cve),
        },
    )


def to_findings(results: Iterable[ToolResult]) -> list[Finding]:
    """Report findings for the tool results, worst first, without duplicates."""
    kept: list[ToolResult] = []
    seen_cves: set[str] = set()
    for result in results:
        if result.severity is Severity.INFO or covered_by_passive_checks(result):
            continue
        if result.cve and result.cve <= seen_cves:
            continue  # the same flaw reported by both tools
        seen_cves |= result.cve
        kept.append(result)
    kept.sort(key=lambda r: (SEVERITY_ORDER.index(r.severity), r.uncertain, r.name))
    return [to_finding(r) for r in kept[:MAX_FINDINGS]]
