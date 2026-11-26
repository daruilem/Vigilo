"""TLS check: certificate validity and expiry, protocol versions, HTTP to HTTPS redirect.

Protocol recommendations follow BSI TR-03116-4 (German Federal Office for Information
Security): TLS 1.2 and 1.3 only. TLS 1.0 and 1.1 are deprecated by RFC 8996.
"""

from __future__ import annotations

import asyncio
import socket
import ssl
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

from vigilo.checks.base import Check, ScanContext
from vigilo.models import Finding, Observation, Severity, Status
from vigilo.net import fetch_page

CHECK = "tls"
CONNECT_TIMEOUT = 8.0
EXPIRY_CRITICAL_DAYS = 14
EXPIRY_WARNING_DAYS = 30

BSI_TLS = "BSI TR-03116-4: TLS 1.2 and TLS 1.3 only"
RFC_8996 = "https://www.rfc-editor.org/rfc/rfc8996"

PROTOCOLS: dict[str, ssl.TLSVersion] = {
    "TLSv1.0": ssl.TLSVersion.TLSv1,
    "TLSv1.1": ssl.TLSVersion.TLSv1_1,
    "TLSv1.2": ssl.TLSVersion.TLSv1_2,
    "TLSv1.3": ssl.TLSVersion.TLSv1_3,
}
LEGACY = ("TLSv1.0", "TLSv1.1")

# True = accepted, False = refused, None = could not be tested from this machine.
ProtocolSupport = dict[str, bool | None]


@dataclass(frozen=True)
class CertificateInfo:
    subject: str
    issuer: str
    not_before: datetime
    not_after: datetime
    san: list[str] = field(default_factory=list)


class TlsCheck(Check):
    name = CHECK
    label = "TLS certificate, protocol versions and HTTPS redirect"
    description = "Checks the certificate, the TLS versions offered and the HTTPS redirect."

    async def run(self, ctx: ScanContext) -> list[Finding]:
        host, port = ctx.target.hostname, ctx.target.port
        # Connect to the address validated at the start of the scan, never to a fresh DNS
        # answer: otherwise the name could be switched to an internal address in between.
        address = ctx.addresses[0] if ctx.addresses else host
        findings: list[Finding] = []
        try:
            cert = await asyncio.to_thread(fetch_certificate, host, port, address)
        except ssl.SSLCertVerificationError as exc:
            findings.append(_invalid_certificate(exc.verify_message or str(exc)))
        except ssl.SSLError:
            raise  # a handshake problem, not a missing HTTPS: reported as "could not check"
        except OSError:
            # Nothing answers on the HTTPS port: the protocol probes would only repeat it.
            return [no_https(ctx.target.https_url), await _https_redirect(ctx)]
        else:
            findings.extend(evaluate_certificate(cert, datetime.now(timezone.utc)))
        probes = await asyncio.gather(
            *(asyncio.to_thread(probe_protocol, host, port, v, address) for v in PROTOCOLS.values())
        )
        findings.extend(evaluate_protocols(dict(zip(PROTOCOLS, probes, strict=True))))
        findings.append(await _https_redirect(ctx))
        return findings


# --- network helpers (thin, not unit-tested) ------------------------------------------


def fetch_certificate(host: str, port: int, address: str) -> CertificateInfo:
    context = ssl.create_default_context()
    with (
        socket.create_connection((address, port), timeout=CONNECT_TIMEOUT) as sock,
        context.wrap_socket(sock, server_hostname=host) as tls,
    ):
        return parse_peer_certificate(tls.getpeercert() or {})


def probe_protocol(host: str, port: int, version: ssl.TLSVersion, address: str) -> bool | None:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        try:
            context.minimum_version = version
            context.maximum_version = version
        except (ValueError, ssl.SSLError):
            return None
    if version < ssl.TLSVersion.TLSv1_2:
        try:
            context.set_ciphers("DEFAULT:@SECLEVEL=0")
        except ssl.SSLError:
            return None
    try:
        with (
            socket.create_connection((address, port), timeout=CONNECT_TIMEOUT) as sock,
            context.wrap_socket(sock, server_hostname=host),
        ):
            return True
    except ssl.SSLError as exc:
        # Raised locally when our own OpenSSL build cannot speak this version at all.
        if exc.reason == "NO_PROTOCOLS_AVAILABLE":
            return None
        return False
    except OSError:
        return False


async def _https_redirect(ctx: ScanContext) -> Finding:
    fid, title = "tls.https-redirect", "Redirect from HTTP to HTTPS"
    request_label = f"GET {ctx.target.http_url}"
    try:
        response = await fetch_page(ctx.http, ctx.target.http_url)
    except httpx.ConnectError:
        return Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.INFO,
            description="The site does not answer on plain HTTP, so visitors cannot land on it.",
            observed=[Observation(label=request_label, value="no answer")],
        )
    final_url = str(response.url)
    if response.url.scheme == "https":
        return Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.PASS,
            description="Visitors typing the address without https:// are sent to the secure site.",
            observed=[Observation(label=request_label, value=f"redirected to {final_url}")],
            evidence={"final_url": final_url},
        )
    return Finding(
        id=fid,
        check=CHECK,
        title=title,
        status=Status.FAIL,
        severity=Severity.MEDIUM,
        description=(
            "Visitors who type the address without https:// stay on an unencrypted page, "
            "where data they enter can be read or modified."
        ),
        recommendation="Redirect every HTTP request to HTTPS with a 301 redirect.",
        observed=[
            Observation(label=request_label, value=f"{response.status_code} · no redirect to HTTPS")
        ],
        evidence={"final_url": final_url},
    )


# --- pure logic (unit-tested) ---------------------------------------------------------


def parse_peer_certificate(raw: dict[str, Any]) -> CertificateInfo:
    """Convert the dict returned by `SSLSocket.getpeercert()` into a CertificateInfo."""

    def name(rdns: Any) -> str:
        attrs = {k: v for rdn in rdns or () for (k, v) in rdn}
        return str(attrs.get("commonName") or attrs.get("organizationName") or "unknown")

    def when(value: str) -> datetime:
        return datetime.fromtimestamp(ssl.cert_time_to_seconds(value), tz=timezone.utc)

    return CertificateInfo(
        subject=name(raw.get("subject")),
        issuer=name(raw.get("issuer")),
        not_before=when(raw["notBefore"]),
        not_after=when(raw["notAfter"]),
        san=[value for kind, value in raw.get("subjectAltName", ()) if kind == "DNS"],
    )


def evaluate_certificate(cert: CertificateInfo, now: datetime) -> list[Finding]:
    evidence = {
        "subject": cert.subject,
        "issuer": cert.issuer,
        "not_after": cert.not_after.isoformat(),
        "san": cert.san,
    }
    valid = Finding(
        id="tls.certificate",
        check=CHECK,
        title="Certificate validity",
        status=Status.PASS,
        description=f"The certificate is valid and issued by a trusted authority ({cert.issuer}).",
        evidence=evidence,
    )
    days_left = (cert.not_after - now).days
    fid, title = "tls.certificate-expiry", "Certificate expiry"
    ev = {"not_after": cert.not_after.isoformat(), "days_left": days_left}
    renew = (
        "Renew the certificate now and enable automatic renewal (for example with "
        "Let's Encrypt / certbot or your hosting provider's auto-renew option)."
    )
    if days_left < EXPIRY_CRITICAL_DAYS:
        expiry = Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.FAIL,
            severity=Severity.HIGH,
            description=(
                f"The certificate expires in {max(days_left, 0)} days. After that, browsers "
                "will show a full-page security warning and most visitors will leave."
            ),
            recommendation=renew,
            evidence=ev,
        )
    elif days_left < EXPIRY_WARNING_DAYS:
        expiry = Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.WARN,
            severity=Severity.MEDIUM,
            description=f"The certificate expires in {days_left} days.",
            recommendation=renew,
            evidence=ev,
        )
    else:
        expiry = Finding(
            id=fid,
            check=CHECK,
            title=title,
            status=Status.PASS,
            description=f"The certificate is valid for another {days_left} days.",
            evidence=ev,
        )
    valid = valid.model_copy(
        update={
            "observed": [
                Observation(label="Issuer", value=cert.issuer),
                Observation(label="Covers", value=", ".join(cert.san) or cert.subject),
            ]
        }
    )
    expiry = expiry.model_copy(
        update={
            "observed": [
                Observation(
                    label="Expires",
                    value=f"{cert.not_after:%Y-%m-%d} ({max(days_left, 0)} days left)",
                )
            ]
        }
    )
    return [valid, expiry]


def no_https(url: str) -> Finding:
    return Finding(
        id="tls.https",
        check=CHECK,
        title="HTTPS availability",
        status=Status.FAIL,
        severity=Severity.CRITICAL,
        description=(
            "Your site cannot be opened over a secure connection. Everything visitors send or "
            "receive, including passwords and form entries, travels unencrypted and can be "
            "read or changed on the way."
        ),
        recommendation=(
            "Serve the site over HTTPS with a valid certificate. Free certificates are "
            "available from Let's Encrypt."
        ),
        observed=[Observation(label=f"GET {url}", value="no answer")],
    )


def _invalid_certificate(reason: str) -> Finding:
    return Finding(
        id="tls.certificate",
        check=CHECK,
        title="Certificate validity",
        status=Status.FAIL,
        severity=Severity.CRITICAL,
        description=(
            "Browsers do not trust this site's certificate and show a security warning to "
            "every visitor. Encrypted traffic could also be intercepted."
        ),
        recommendation=(
            "Install a valid certificate that covers this exact domain name, including the "
            "full certificate chain. Free certificates are available from Let's Encrypt."
        ),
        observed=[Observation(label="Certificate error", value=reason)],
        evidence={"reason": reason},
    )


def evaluate_protocols(support: ProtocolSupport) -> list[Finding]:
    refs = [BSI_TLS, RFC_8996]
    findings: list[Finding] = []
    accepted_legacy = [p for p in LEGACY if support.get(p) is True]
    untested_legacy = [p for p in LEGACY if support.get(p) is None]
    fid, title = "tls.legacy-protocols", "Obsolete TLS versions"
    if accepted_legacy:
        findings.append(
            Finding(
                id=fid,
                check=CHECK,
                title=title,
                status=Status.FAIL,
                severity=Severity.HIGH,
                description=(
                    f"The server still accepts {' and '.join(accepted_legacy)}, which have known "
                    "weaknesses and are no longer considered secure."
                ),
                recommendation="Disable TLS 1.0 and 1.1 and keep only TLS 1.2 and TLS 1.3.",
                references=refs,
                evidence={"accepted": accepted_legacy},
            )
        )
    elif untested_legacy:
        findings.append(
            Finding(
                id=fid,
                check=CHECK,
                title=title,
                status=Status.INFO,
                description=(
                    f"{' and '.join(untested_legacy)} could not be tested because the scanning "
                    "machine's TLS library no longer supports them."
                ),
                references=refs,
                evidence={"untested": untested_legacy},
            )
        )
    else:
        findings.append(
            Finding(
                id=fid,
                check=CHECK,
                title=title,
                status=Status.PASS,
                description="Obsolete TLS versions (1.0 and 1.1) are refused.",
                references=refs,
            )
        )
    fid, title = "tls.modern-protocols", "Modern TLS versions"
    tls12, tls13 = support.get("TLSv1.2"), support.get("TLSv1.3")
    if tls12 is not True and tls13 is not True:
        findings.append(
            Finding(
                id=fid,
                check=CHECK,
                title=title,
                status=Status.FAIL,
                severity=Severity.CRITICAL,
                description=(
                    "The server offers neither TLS 1.2 nor TLS 1.3, so modern browsers "
                    "cannot connect securely."
                ),
                recommendation="Enable TLS 1.2 and TLS 1.3 on the web server.",
                references=refs,
                evidence={"TLSv1.2": tls12, "TLSv1.3": tls13},
            )
        )
    elif tls13 is not True:
        findings.append(
            Finding(
                id=fid,
                check=CHECK,
                title=title,
                status=Status.WARN,
                severity=Severity.LOW,
                description="TLS 1.3, the fastest and most secure version, is not offered.",
                recommendation="Enable TLS 1.3 (supported by all current web servers and hosts).",
                references=refs,
                evidence={"TLSv1.2": tls12, "TLSv1.3": tls13},
            )
        )
    else:
        findings.append(
            Finding(
                id=fid,
                check=CHECK,
                title=title,
                status=Status.PASS,
                description="The server supports TLS 1.3.",
                references=refs,
                evidence={"TLSv1.2": tls12, "TLSv1.3": tls13},
            )
        )
    return [_with_protocol_observations(f, support) for f in findings]


def _support_label(value: bool | None) -> str:
    return {True: "accepted", False: "refused", None: "not testable"}[value]


def _with_protocol_observations(finding: Finding, support: ProtocolSupport) -> Finding:
    versions = LEGACY if finding.id == "tls.legacy-protocols" else ("TLSv1.2", "TLSv1.3")
    observed = [Observation(label=v, value=_support_label(support.get(v))) for v in versions]
    return finding.model_copy(update={"observed": observed})
