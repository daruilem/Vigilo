"""HTTP security headers check."""

from __future__ import annotations

import re
from collections.abc import Mapping

import httpx

from vigilo.checks.base import Check, ScanContext
from vigilo.models import Finding, Observation, Severity, Status

CHECK = "headers"
HSTS_RECOMMENDED_MAX_AGE = 31_536_000  # one year, in seconds
OWASP_HEADERS = "https://owasp.org/www-project-secure-headers/"
MDN = "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/"

_VERSION_PATTERN = re.compile(r"\d+\.\d+")


def parse_csp(policy: str) -> dict[str, list[str]]:
    """Parse a CSP header into {directive: [sources]}. The first occurrence of a directive wins."""
    directives: dict[str, list[str]] = {}
    for part in policy.split(";"):
        tokens = part.strip().lower().split()
        if tokens and tokens[0] not in directives:
            directives[tokens[0]] = tokens[1:]
    return directives


def unsafe_script_sources(policy: str) -> list[str]:
    """Unsafe keywords that actually weaken script execution rules.

    Only `script-src` matters for scripts (falling back to `default-src`). Browsers ignore
    'unsafe-inline' when a nonce or hash is also present, so it is not reported then.
    """
    directives = parse_csp(policy)
    sources = directives.get("script-src", directives.get("default-src"))
    if sources is None:
        return []
    has_nonce_or_hash = any(
        s.startswith(("'nonce-", "'sha256-", "'sha384-", "'sha512-")) for s in sources
    )
    unsafe = []
    if "'unsafe-inline'" in sources and not has_nonce_or_hash:
        unsafe.append("'unsafe-inline'")
    if "'unsafe-eval'" in sources:
        unsafe.append("'unsafe-eval'")
    return unsafe


class HeadersCheck(Check):
    name = CHECK
    label = "HTTP security headers"
    description = "Checks the HTTP security headers returned by the home page."

    async def run(self, ctx: ScanContext) -> list[Finding]:
        if ctx.homepage is None:
            return [_unavailable()]
        return evaluate_headers(ctx.homepage.headers)


# Which raw headers each finding shows under "Observed", with their usual spelling.
OBSERVED_HEADERS: dict[str, tuple[str, ...]] = {
    "headers.hsts": ("Strict-Transport-Security",),
    "headers.csp": ("Content-Security-Policy",),
    "headers.clickjacking": ("X-Frame-Options", "Content-Security-Policy"),
    "headers.nosniff": ("X-Content-Type-Options",),
    "headers.referrer-policy": ("Referrer-Policy",),
    "headers.permissions-policy": ("Permissions-Policy",),
    "headers.server-disclosure": ("Server", "X-Powered-By"),
}
NOT_SENT = "not sent"


def evaluate_headers(headers: Mapping[str, str]) -> list[Finding]:
    """Turn a set of response headers into findings. Pure function, no I/O."""
    h = httpx.Headers(headers)
    csp = h.get("content-security-policy")
    findings = [
        _hsts(h.get("strict-transport-security")),
        _csp(csp),
        _clickjacking(h.get("x-frame-options"), csp),
        _nosniff(h.get("x-content-type-options")),
        _referrer_policy(h.get("referrer-policy")),
        _permissions_policy(h.get("permissions-policy")),
        _server_disclosure(h),
    ]
    return [_with_observed(f, h) for f in findings]


def _with_observed(finding: Finding, h: httpx.Headers) -> Finding:
    names = OBSERVED_HEADERS.get(finding.id, ())
    observed = [Observation(label=name, value=h.get(name) or NOT_SENT) for name in names]
    return finding.model_copy(update={"observed": observed})


def _unavailable() -> Finding:
    return Finding(
        id="headers.unavailable",
        check=CHECK,
        title="HTTP security headers",
        status=Status.INFO,
        description=(
            "The headers could not be read because the secure version of the site did not "
            "load. Fix the certificate first, then check again."
        ),
    )


def _hsts(value: str | None) -> Finding:
    fid, title = "headers.hsts", "HTTP Strict Transport Security (HSTS)"
    refs = [MDN + "Strict-Transport-Security", OWASP_HEADERS]
    if value is None:
        return Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.FAIL,
            severity=Severity.MEDIUM,
            description=(
                "Browsers are not told to always use a secure connection. A visitor on a "
                "public Wi-Fi can be silently downgraded to an unencrypted connection."
            ),
            recommendation=(
                "Send 'Strict-Transport-Security: max-age=31536000; includeSubDomains' "
                "on every HTTPS response."
            ),
            references=refs,
        )

    match = re.search(r"max-age\s*=\s*\"?(\d+)", value, re.IGNORECASE)
    max_age = int(match.group(1)) if match else 0
    evidence = {"header": value, "max_age": max_age}
    if max_age < HSTS_RECOMMENDED_MAX_AGE:
        return Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.WARN,
            severity=Severity.LOW,
            description=(
                "HSTS is enabled, but for a short period, so the protection expires quickly "
                "for returning visitors."
            ),
            recommendation="Raise max-age to at least 31536000 (one year).",
            references=refs,
            evidence=evidence,
        )
    return Finding(
        id=fid,
        check=CHECK,
        title=title,
        status=Status.PASS,
        description="Browsers are told to always use a secure connection to this site.",
        references=refs,
        evidence=evidence,
    )


def _csp(value: str | None) -> Finding:
    fid, title = "headers.csp", "Content Security Policy (CSP)"
    refs = [MDN + "Content-Security-Policy", OWASP_HEADERS]
    if value is None:
        return Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.FAIL,
            severity=Severity.MEDIUM,
            description=(
                "There is no Content Security Policy. If an attacker manages to inject a "
                "script (for example through a vulnerable plugin), nothing limits what it "
                "can load or do."
            ),
            recommendation=(
                "Define a Content-Security-Policy listing the sources your site really "
                "uses. Start in report-only mode to avoid breaking the site."
            ),
            references=refs,
        )

    unsafe = unsafe_script_sources(value)
    if unsafe:
        return Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.WARN,
            severity=Severity.LOW,
            description=(
                f"A CSP is present but allows {', '.join(unsafe)}, which removes most of its "
                "protection against injected scripts."
            ),
            recommendation=(
                "Replace inline scripts with nonces or hashes, then drop these keywords."
            ),
            references=refs,
            evidence={"header": value, "unsafe_keywords": unsafe},
        )
    return Finding(
        id=fid,
        check=CHECK,
        title=title,
        status=Status.PASS,
        description="A Content Security Policy restricts what the page can load.",
        references=refs,
        evidence={"header": value},
    )


def _clickjacking(xfo: str | None, csp: str | None) -> Finding:
    fid, title = "headers.clickjacking", "Clickjacking protection"
    refs = [MDN + "X-Frame-Options", MDN + "Content-Security-Policy/frame-ancestors"]
    has_frame_ancestors = csp is not None and "frame-ancestors" in csp.lower()
    xfo_ok = xfo is not None and xfo.strip().upper() in ("DENY", "SAMEORIGIN")
    if has_frame_ancestors or xfo_ok:
        return Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.PASS,
            description="Other websites cannot display this site inside a hidden frame.",
            references=refs,
            evidence={"x_frame_options": xfo, "csp_frame_ancestors": has_frame_ancestors},
        )
    return Finding(
        id=fid,
        check=CHECK,
        title=title,
        status=Status.FAIL,
        severity=Severity.MEDIUM,
        description=(
            "Another website can display this site inside an invisible frame and trick "
            "visitors into clicking buttons they cannot see (clickjacking)."
        ),
        recommendation=(
            "Send 'X-Frame-Options: SAMEORIGIN' or add \"frame-ancestors 'self'\" to the CSP."
        ),
        references=refs,
    )


def _nosniff(value: str | None) -> Finding:
    fid, title = "headers.nosniff", "MIME type sniffing protection"
    refs = [MDN + "X-Content-Type-Options"]
    if value is not None and value.strip().lower() == "nosniff":
        return Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.PASS,
            description="Browsers will not guess file types, which blocks a class of attacks.",
            references=refs,
        )
    return Finding(
        id=fid,
        check=CHECK,
        title=title,
        status=Status.FAIL,
        severity=Severity.LOW,
        description=(
            "Browsers may guess the type of downloaded files, which can turn an uploaded "
            "file into executable script."
        ),
        recommendation="Send 'X-Content-Type-Options: nosniff'.",
        references=refs,
        evidence={"header": value},
    )


def _referrer_policy(value: str | None) -> Finding:
    fid, title = "headers.referrer-policy", "Referrer policy"
    refs = [MDN + "Referrer-Policy"]
    weak = {"unsafe-url", "no-referrer-when-downgrade"}
    if value is None:
        return Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.FAIL,
            severity=Severity.LOW,
            description=(
                "No referrer policy is set, so the browser default decides how much of the "
                "page address is shared with other sites."
            ),
            recommendation="Send 'Referrer-Policy: strict-origin-when-cross-origin'.",
            references=refs,
        )
    # The header can hold a fallback list; the last recognised value wins.
    effective = value.split(",")[-1].strip().lower()
    if effective in weak:
        return Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.WARN,
            severity=Severity.LOW,
            description=(
                "Full page addresses, possibly with private parameters, leak to other sites."
            ),
            recommendation="Use 'strict-origin-when-cross-origin' or stricter.",
            references=refs,
            evidence={"header": value},
        )
    return Finding(
        id=fid,
        check=CHECK,
        title=title,
        status=Status.PASS,
        description="The site limits what it shares about visited pages with other sites.",
        references=refs,
        evidence={"header": value},
    )


def _permissions_policy(value: str | None) -> Finding:
    fid, title = "headers.permissions-policy", "Permissions policy"
    refs = [MDN + "Permissions-Policy"]
    if value is None:
        return Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.FAIL,
            severity=Severity.LOW,
            description=(
                "The site does not restrict access to browser features such as the camera, "
                "microphone or location for embedded content."
            ),
            recommendation=(
                "Send a Permissions-Policy disabling unused features, e.g. "
                "'camera=(), microphone=(), geolocation=()'."
            ),
            references=refs,
        )
    return Finding(
        id=fid,
        check=CHECK,
        title=title,
        status=Status.PASS,
        description="Access to sensitive browser features is restricted.",
        references=refs,
        evidence={"header": value},
    )


def _server_disclosure(h: httpx.Headers) -> Finding:
    fid, title = "headers.server-disclosure", "Software version disclosure"
    leaks = {
        name: h[name]
        for name in ("server", "x-powered-by", "x-aspnet-version", "x-generator")
        if name in h and _VERSION_PATTERN.search(h[name])
    }
    if leaks:
        return Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.WARN,
            severity=Severity.LOW,
            description=(
                "The server announces the exact software versions it runs. This helps "
                "attackers find known vulnerabilities quickly."
            ),
            recommendation="Hide version numbers in the web server and application configuration.",
            evidence=leaks,
        )
    return Finding(
        id=fid,
        check=CHECK,
        title=title,
        status=Status.PASS,
        description="The server does not reveal software version numbers.",
    )
