"""Email security check: SPF, DMARC and DKIM records in public DNS.

These records decide whether a criminal can send emails that look like they come from
the site's domain, a very common attack on small businesses (fake invoices, password
resets). Only public DNS records are read.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

import dns.asyncresolver
import dns.exception
import dns.resolver

from vigilo.checks.base import Check, ScanContext
from vigilo.models import Finding, Fix, Observation, Platform, Severity, Status

CHECK = "email"
DNS_TIMEOUT = 5.0
SPF_LOOKUP_LIMIT = 10  # RFC 7208 section 4.6.4
DKIM_SELECTORS = (
    "default", "google", "selector1", "selector2", "k1", "k2", "mail", "dkim",
    "s1", "s2", "smtp", "mxvault", "zoho", "protonmail", "everlytickey1",
)  # fmt: skip

# Known mail providers, recognised from MX hosts, and the SPF include they document.
PROVIDERS: tuple[tuple[str, str, str], ...] = (
    ("google.com", "Google Workspace", "include:_spf.google.com"),
    ("googlemail.com", "Google Workspace", "include:_spf.google.com"),
    ("protection.outlook.com", "Microsoft 365", "include:spf.protection.outlook.com"),
    ("ovh.net", "OVHcloud", "include:mx.ovh.com"),
    ("zoho.eu", "Zoho Mail", "include:zohomail.eu"),
    ("zoho.com", "Zoho Mail", "include:zohomail.com"),
    ("ionos.", "IONOS", "include:_spf-eu.ionos.com"),
    ("protonmail.ch", "Proton Mail", "include:_spf.protonmail.ch"),
)
UNKNOWN_INCLUDE = "include:YOUR-MAIL-PROVIDER"


@dataclass
class EmailRecords:
    domain: str
    mx: list[str] = field(default_factory=list)
    spf: list[str] = field(default_factory=list)
    dmarc: list[str] = field(default_factory=list)
    dkim_selectors: list[str] = field(default_factory=list)
    # DNS lookups needed by the whole SPF chain (includes followed). None: not measured.
    spf_lookups: int | None = None


class EmailCheck(Check):
    name = CHECK
    label = "Email security (SPF, DMARC, DKIM)"
    description = "Checks that criminals cannot easily send emails in the domain's name."

    async def run(self, ctx: ScanContext) -> list[Finding]:
        domain = mail_domain(ctx.target.hostname)
        records = await fetch_records(domain)
        return evaluate(records)


def mail_domain(hostname: str) -> str:
    """Emails use the bare domain: www.shop.example sends as shop.example."""
    return hostname[4:] if hostname.startswith("www.") else hostname


# --- DNS (thin, not unit-tested) ------------------------------------------------------


async def _txt(resolver: dns.asyncresolver.Resolver, name: str) -> list[str]:
    try:
        answer = await resolver.resolve(name, "TXT")
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return []
    return [b"".join(r.strings).decode("utf-8", "replace") for r in answer]


async def _mx(resolver: dns.asyncresolver.Resolver, name: str) -> list[str]:
    try:
        answer = await resolver.resolve(name, "MX")
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return []
    return sorted(str(r.exchange).rstrip(".").lower() for r in answer)


async def fetch_records(domain: str) -> EmailRecords:
    resolver = dns.asyncresolver.Resolver()
    resolver.lifetime = DNS_TIMEOUT
    mx, txt, dmarc, *dkim = await asyncio.gather(
        _mx(resolver, domain),
        _txt(resolver, domain),
        _txt(resolver, f"_dmarc.{domain}"),
        *(_txt(resolver, f"{s}._domainkey.{domain}") for s in DKIM_SELECTORS),
    )
    spf = [r for r in txt if r.lower().startswith("v=spf1")]
    lookups = None
    if len(spf) == 1:
        lookups = await count_spf_lookups(spf[0], lambda name: _txt(resolver, name))
    return EmailRecords(
        domain=domain,
        mx=mx,
        spf=spf,
        spf_lookups=lookups,
        dmarc=[r for r in dmarc if r.lower().replace(" ", "").startswith("v=dmarc1")],
        dkim_selectors=[
            s
            for s, answers in zip(DKIM_SELECTORS, dkim, strict=True)
            if any("p=" in a for a in answers)
        ],
    )


# --- pure logic (unit-tested) ---------------------------------------------------------


def provider_for(mx: list[str]) -> tuple[str, str] | None:
    for host in mx:
        for suffix, name, include in PROVIDERS:
            if suffix in host:
                return name, include
    return None


def spf_all_qualifier(record: str) -> str | None:
    """The qualifier of the final 'all' mechanism: '-', '~', '?', '+' or None if absent."""
    for term in record.lower().split()[1:]:
        match = re.fullmatch(r"([-~?+]?)all", term)
        if match:
            return match.group(1) or "+"
    return None


def spf_lookup_count(record: str) -> int:
    """DNS lookups caused directly by this record (nested includes are not followed)."""
    count = 0
    for term in record.lower().split()[1:]:
        term = term.lstrip("-~?+")
        if term.startswith(("include:", "a", "mx", "ptr", "exists:", "redirect=")):
            if term in ("all",) or term.startswith("all"):
                continue
            count += 1
    return count


async def count_spf_lookups(
    record: str, fetch_txt: Callable[[str], Awaitable[list[str]]], max_depth: int = 10
) -> int:
    """DNS lookups needed to evaluate an SPF record, following include and redirect.

    Stops counting as soon as the limit is exceeded, and never visits a domain twice, so a
    record that includes itself cannot make the check loop.
    """
    total = 0
    seen: set[str] = set()

    async def walk(current: str, depth: int) -> None:
        nonlocal total
        for term in current.lower().split()[1:]:
            if total > SPF_LOOKUP_LIMIT:
                return
            term = term.lstrip("-~?+")
            target = None
            if term.startswith("include:"):
                target = term.split(":", 1)[1]
            elif term.startswith("redirect="):
                target = term.split("=", 1)[1]
            elif term in ("a", "mx", "ptr") or term.startswith(
                ("a:", "a/", "mx:", "mx/", "ptr:", "exists:")
            ):
                total += 1
                continue
            else:
                continue
            total += 1
            if target and depth < max_depth and target not in seen:
                seen.add(target)
                child = [r for r in await fetch_txt(target) if r.lower().startswith("v=spf1")]
                if child:
                    await walk(child[0], depth + 1)

    await walk(record, 0)
    return total


def dmarc_tags(record: str) -> dict[str, str]:
    tags = {}
    for part in record.split(";"):
        if "=" in part:
            key, _, value = part.partition("=")
            tags[key.strip().lower()] = value.strip().lower()
    return tags


def _dns_fixes(name: str, value: str) -> dict[Platform, Fix]:
    record = f'{name}.  TXT  "{value}"'
    return {
        Platform.APACHE: Fix(
            intro=(
                "Email records live in DNS, not on the web server. Add this TXT record at "
                "your DNS provider (often where you bought the domain):"
            ),
            code=record,
        ),
        Platform.NGINX: Fix(
            intro=(
                "Email records live in DNS, not on the web server. Add this TXT record at "
                "your DNS provider (often where you bought the domain):"
            ),
            code=record,
        ),
        Platform.CLOUDFLARE: Fix(
            intro="DNS, then Records, then Add record. Type TXT, with this name and content:",
            code=f"Name:    {name}\nContent: {value}",
        ),
        Platform.WORDPRESS: Fix(
            intro=(
                "If your domain is managed by your WordPress host, open its DNS zone editor "
                "and add this TXT record:"
            ),
            code=record,
        ),
    }


def evaluate(records: EmailRecords) -> list[Finding]:
    return [_spf(records), _dmarc(records), _dkim(records)]


def _spf(r: EmailRecords) -> Finding:
    fid, title = "email.spf", "SPF record"
    observed = [Observation(label=f"TXT {r.domain}", value=r.spf[0] if r.spf else "no SPF record")]
    provider = provider_for(r.mx)
    include = provider[1] if provider else UNKNOWN_INCLUDE
    suggested = f"v=spf1 {include} -all" if r.mx else "v=spf1 -all"
    note = (
        f"Mail provider recognised from MX records: {provider[0]}."
        if provider
        else (
            "This domain has no MX record, so it should not send emails at all."
            if not r.mx
            else None
        )
    )

    if not r.spf:
        return Finding(
            id=fid, check=CHECK, title=title, status=Status.FAIL, severity=Severity.MEDIUM,
            description=(
                "Nothing tells email services which servers may send emails for this domain. "
                "A criminal can send fake invoices or messages that look like they come from you."
            ),
            recommendation="Publish an SPF record listing the services that send your emails.",
            observed=observed, note=note, fixes=_dns_fixes(r.domain, suggested),
        )  # fmt: skip
    if len(r.spf) > 1:
        return Finding(
            id=fid, check=CHECK, title=title, status=Status.FAIL, severity=Severity.MEDIUM,
            description=(
                "The domain has several SPF records. Email services then ignore all of them, "
                "as if there were none."
            ),
            recommendation="Merge them into a single SPF record.",
            observed=[Observation(label=f"TXT {r.domain}", value=v) for v in r.spf],
            fixes=_dns_fixes(r.domain, suggested),
        )  # fmt: skip

    record = r.spf[0]
    qualifier = spf_all_qualifier(record)
    lookups = r.spf_lookups if r.spf_lookups is not None else spf_lookup_count(record)
    fixed = re.sub(r"\s[-~?+]?all\b", "", record).strip() + " -all"

    if qualifier == "+":
        return Finding(
            id=fid, check=CHECK, title=title, status=Status.FAIL, severity=Severity.HIGH,
            description=(
                "The SPF record ends with '+all', which allows every server in the world to "
                "send emails in your name. It is worse than having no record."
            ),
            observed=observed, fixes=_dns_fixes(r.domain, fixed),
        )  # fmt: skip
    if lookups > SPF_LOOKUP_LIMIT:
        return Finding(
            id=fid, check=CHECK, title=title, status=Status.FAIL, severity=Severity.MEDIUM,
            description=(
                f"The SPF record needs {lookups} DNS lookups. Above {SPF_LOOKUP_LIMIT}, email "
                "services treat it as broken."
            ),
            recommendation="Remove services that no longer send emails for you.",
            observed=observed,
        )  # fmt: skip
    if qualifier in ("?", None):
        return Finding(
            id=fid, check=CHECK, title=title, status=Status.WARN, severity=Severity.MEDIUM,
            description=(
                "The SPF record does not say what to do with emails from other servers, so "
                "fake emails are not treated as suspicious."
            ),
            observed=observed, fixes=_dns_fixes(r.domain, fixed),
        )  # fmt: skip
    return Finding(
        id=fid, check=CHECK, title=title, status=Status.PASS,
        description="The domain lists the servers allowed to send its emails.",
        observed=observed, note=note,
    )  # fmt: skip


def _dmarc(r: EmailRecords) -> Finding:
    fid, title = "email.dmarc", "DMARC record"
    name = f"_dmarc.{r.domain}"
    observed = [
        Observation(label=f"TXT {name}", value=r.dmarc[0] if r.dmarc else "no DMARC record")
    ]
    suggested = f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{r.domain}"

    if not r.dmarc:
        return Finding(
            id=fid, check=CHECK, title=title, status=Status.FAIL, severity=Severity.MEDIUM,
            description=(
                "Email services are not told what to do with emails that fail the checks, so "
                "fake emails in your name usually still reach the inbox."
            ),
            recommendation="Publish a DMARC record with a quarantine or reject policy.",
            observed=observed, fixes=_dns_fixes(name, suggested),
        )  # fmt: skip

    tags = dmarc_tags(r.dmarc[0])
    policy = tags.get("p", "none")
    pct = tags.get("pct", "100")
    if policy == "none":
        return Finding(
            id=fid, check=CHECK, title=title, status=Status.WARN, severity=Severity.LOW,
            description=(
                "DMARC is in monitoring mode (p=none): fake emails are reported to you but "
                "still delivered."
            ),
            observed=observed, fixes=_dns_fixes(name, suggested),
        )  # fmt: skip
    if pct != "100":
        return Finding(
            id=fid, check=CHECK, title=title, status=Status.WARN, severity=Severity.LOW,
            description=f"The DMARC policy only applies to {pct}% of failing emails.",
            observed=observed,
            fixes=_dns_fixes(name, re.sub(r"pct=\d+", "pct=100", r.dmarc[0])),
        )  # fmt: skip
    return Finding(
        id=fid, check=CHECK, title=title, status=Status.PASS,
        description=f"Emails that fail the checks are {'rejected' if policy == 'reject' else 'sent to spam'}.",
        observed=observed,
    )  # fmt: skip


def _dkim(r: EmailRecords) -> Finding:
    fid, title = "email.dkim", "DKIM signature"
    if r.dkim_selectors:
        return Finding(
            id=fid, check=CHECK, title=title, status=Status.PASS,
            description="Emails from this domain can be signed, which proves they were not altered.",
            observed=[Observation(label="Selectors found", value=", ".join(r.dkim_selectors))],
        )  # fmt: skip
    return Finding(
        id=fid, check=CHECK, title=title, status=Status.INFO,
        description=(
            "No DKIM key was found among the common names. Your provider may use another "
            "name: check its settings to make sure outgoing emails are signed."
        ),
        observed=[
            Observation(label="Selectors tried", value=f"{len(DKIM_SELECTORS)} common names")
        ],
    )  # fmt: skip
