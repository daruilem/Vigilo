"""Proof of domain ownership, required before any active scan.

A passive check only reads what a website shows every visitor, so a confirmation box is
enough. An active scan sends test requests, and running one against a site without the
owner's permission is a criminal offence in most countries (for example section 202c of
the German Criminal Code). Vigilo therefore asks for a proof that only someone who
controls the domain can give:

1. HTML tag: `<meta name="vigilo-verification" content="<code>">` in the <head> of the home
   page (the easiest for sites built with a CMS: most have a "header code" setting),
2. File: `https://<domain>/vigilo-<id>.txt` at the root of the site, containing the code,
3. DNS: a TXT record `_vigilo.<domain>` with the value `vigilo-verification=<code>`.

These are the methods used to verify a site in Google Search Console, so web developers
know them. The owner usually forwards the request to whoever runs their site, and Vigilo
then checks all three methods by itself (`verify_any`), so nobody has to say which one
was used.

Nothing is stored on the server. The verification code carries its own expiry date and
an HMAC signature bound to the domain, so Vigilo can check that it issued the code for
that domain without remembering it. A successful verification returns an ownership
pass built the same way: signed, bound to the domain and valid for 24 hours.

Scope is the exact host name that was verified: proving `example.com` does not allow
scanning `shop.example.com`, and the other way round.
"""

from __future__ import annotations

import hmac
import secrets
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlsplit

import dns.asyncresolver
import dns.exception
import dns.resolver
import httpx

from vigilo import errors
from vigilo.errors import ScanError
from vigilo.htmlscan import read_page
from vigilo.net import fetch_page, make_client
from vigilo.signing import tag

CHALLENGE_LIFETIME = 24 * 3600
PASS_LIFETIME = 24 * 3600
RECORD_LABEL = "_vigilo"
RECORD_PREFIX = "vigilo-verification="
FILE_PREFIX = "vigilo-"
MAX_FILE_BYTES = 1024
META_NAME = "vigilo-verification"
MAX_PAGE_BYTES = 1_000_000
DNS_TIMEOUT = 5.0

_CHALLENGE = "ownership-challenge"
_PROOF = "ownership-proof"
_CHALLENGE_TAG_LENGTH = 32  # 128 bits: plenty for a code that lives 24 hours, and short to copy


class Method(str, Enum):
    META = "meta"
    FILE = "file"
    DNS = "dns"


class OwnershipError(ScanError):
    code = "not_verified"


@dataclass(frozen=True)
class Challenge:
    domain: str
    token: str
    expires_at: int

    @property
    def dns_name(self) -> str:
        return f"{RECORD_LABEL}.{self.domain}"

    @property
    def dns_value(self) -> str:
        return RECORD_PREFIX + self.token

    @property
    def file_name(self) -> str:
        return f"{FILE_PREFIX}{self.token.split('.', 1)[0]}.txt"

    @property
    def file_url(self) -> str:
        return f"https://{self.domain}/{self.file_name}"

    @property
    def meta_tag(self) -> str:
        return f'<meta name="{META_NAME}" content="{self.token}">'


@dataclass(frozen=True)
class OwnershipPass:
    domain: str
    method: Method
    token: str
    expires_at: int


def _now(now: float | None) -> int:
    return int(time.time() if now is None else now)


# --- Signed values -------------------------------------------------------------------


def create_challenge(domain: str, *, now: float | None = None) -> Challenge:
    expires = _now(now) + CHALLENGE_LIFETIME
    nonce = secrets.token_urlsafe(16)  # never contains "."
    mac = tag(_CHALLENGE, domain, nonce, str(expires))[:_CHALLENGE_TAG_LENGTH]
    return Challenge(domain=domain, token=f"{nonce}.{expires}.{mac}", expires_at=expires)


def _expiry(token: str) -> tuple[str, int, str] | None:
    parts = token.split(".")
    if len(parts) != 3 or not parts[1].isdigit():
        return None
    return parts[0], int(parts[1]), parts[2]


def check_challenge(domain: str, token: str, *, now: float | None = None) -> bool:
    """True if Vigilo issued `token` for `domain` and it has not expired."""
    parsed = _expiry(token)
    if parsed is None:
        return False
    nonce, expires, mac = parsed
    expected = tag(_CHALLENGE, domain, nonce, str(expires))[:_CHALLENGE_TAG_LENGTH]
    return hmac.compare_digest(expected, mac) and _now(now) < expires


def issue_pass(domain: str, method: Method, *, now: float | None = None) -> OwnershipPass:
    expires = _now(now) + PASS_LIFETIME
    mac = tag(_PROOF, domain, method.value, str(expires))
    return OwnershipPass(
        domain=domain,
        method=method,
        token=f"{method.value}.{expires}.{mac}",
        expires_at=expires,
    )


def check_pass(domain: str, token: str, *, now: float | None = None) -> Method | None:
    """The proof method if `token` is a valid ownership pass for `domain`, else None."""
    parsed = _expiry(token)
    if parsed is None:
        return None
    method_name, expires, mac = parsed
    try:
        method = Method(method_name)
    except ValueError:
        return None
    expected = tag(_PROOF, domain, method.value, str(expires))
    if hmac.compare_digest(expected, mac) and _now(now) < expires:
        return method
    return None


# --- Verification (network) ------------------------------------------------------------

TxtLookup = Callable[[str], Awaitable[list[str]]]


async def lookup_txt(name: str) -> list[str]:
    resolver = dns.asyncresolver.Resolver()
    resolver.lifetime = DNS_TIMEOUT
    try:
        answer = await resolver.resolve(name, "TXT")
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return []
    except dns.exception.DNSException as exc:  # timeout, no reachable name server
        raise OwnershipError(errors.DNS_UNAVAILABLE, "dns_unavailable") from exc
    return [b"".join(r.strings).decode("utf-8", "replace") for r in answer]


async def _verify_dns(challenge: Challenge, lookup: TxtLookup) -> None:
    values = [v.strip() for v in await lookup(challenge.dns_name)]
    if any(hmac.compare_digest(v, challenge.dns_value) for v in values):
        return
    found = [v for v in values if v.startswith(RECORD_PREFIX)]
    if found:
        raise OwnershipError(
            errors.RECORD_MISMATCH.format(name=challenge.dns_name), "record_mismatch"
        )
    raise OwnershipError(
        errors.RECORD_NOT_FOUND.format(name=challenge.dns_name), "record_not_found"
    )


async def _verify_file(
    challenge: Challenge, http: httpx.AsyncClient, base_url: str | None = None
) -> None:
    # `base_url` is only set for a lab host (see vigilo.lab), reached at a local address.
    url = f"{base_url}/{challenge.file_name}" if base_url else challenge.file_url
    expected_host = urlsplit(url).hostname
    try:
        response = await fetch_page(http, url, MAX_FILE_BYTES)
    except httpx.TooManyRedirects as exc:
        raise OwnershipError(errors.TOO_MANY_REDIRECTS, "too_many_redirects") from exc
    except httpx.TimeoutException as exc:
        raise OwnershipError(errors.TIMEOUT, "timeout") from exc
    except httpx.TransportError as exc:
        raise OwnershipError(errors.UNREACHABLE, "unreachable") from exc

    # A redirect to another host would prove control of that host, not of this domain.
    if response.request.url.host != expected_host:
        raise OwnershipError(
            errors.FILE_REDIRECTED.format(url=url, hostname=challenge.domain), "file_redirected"
        )
    if response.status_code != 200:
        raise OwnershipError(errors.FILE_NOT_FOUND.format(url=url), "file_not_found")
    content = response.content.decode("utf-8", "replace").strip()
    if not hmac.compare_digest(content, challenge.token):
        raise OwnershipError(errors.FILE_MISMATCH.format(url=url), "file_mismatch")


async def _verify_meta(
    challenge: Challenge, http: httpx.AsyncClient, base_url: str | None = None
) -> None:
    url = f"{base_url}/" if base_url else f"https://{challenge.domain}/"
    expected_host = urlsplit(url).hostname
    try:
        response = await fetch_page(http, url, MAX_PAGE_BYTES)
    except httpx.TooManyRedirects as exc:
        raise OwnershipError(errors.TOO_MANY_REDIRECTS, "too_many_redirects") from exc
    except httpx.TimeoutException as exc:
        raise OwnershipError(errors.TIMEOUT, "timeout") from exc
    except httpx.TransportError as exc:
        raise OwnershipError(errors.UNREACHABLE, "unreachable") from exc

    final_host = response.request.url.host
    if final_host != expected_host:
        # Typically example.com -> www.example.com: the tag proves control of www only.
        raise OwnershipError(
            errors.PAGE_REDIRECTED.format(domain=challenge.domain, other=final_host),
            "page_redirected",
        )
    codes = read_page(response.content.decode("utf-8", "replace")).verification_codes
    if any(hmac.compare_digest(code, challenge.token) for code in codes):
        return
    if codes:
        raise OwnershipError(errors.META_MISMATCH.format(domain=challenge.domain), "meta_mismatch")
    raise OwnershipError(errors.META_NOT_FOUND.format(domain=challenge.domain), "meta_not_found")


async def verify_ownership(
    domain: str,
    token: str,
    method: Method,
    *,
    lookup: TxtLookup = lookup_txt,
    http: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    now: float | None = None,
) -> OwnershipPass:
    """Check the proof for `domain` and return an ownership pass, or raise OwnershipError.

    The code is checked before any network activity, so Vigilo only ever contacts a
    domain for which it issued a code itself.
    """
    parsed = _expiry(token)
    if parsed is None or not check_challenge(domain, token, now=now):
        raise OwnershipError(errors.INVALID_CHALLENGE, "invalid_challenge")
    challenge = Challenge(domain=domain, token=token, expires_at=parsed[1])

    if method is Method.DNS:
        await _verify_dns(challenge, lookup)
        return issue_pass(domain, method, now=now)
    check = _verify_file if method is Method.FILE else _verify_meta
    if http is not None:
        await check(challenge, http, base_url)
    else:
        async with make_client() as client:
            await check(challenge, client, base_url)
    return issue_pass(domain, method, now=now)


async def verify_any(
    domain: str,
    token: str,
    *,
    lookup: TxtLookup = lookup_txt,
    http: httpx.AsyncClient | None = None,
    base_url: str | None = None,
    now: float | None = None,
) -> OwnershipPass:
    """Look for the code with every method, easiest first, and accept the first found.

    The owner often forwards the request to their web developer, who picks a method: the
    owner's page then simply waits, checking again from time to time.
    """
    if not check_challenge(domain, token, now=now):
        raise OwnershipError(errors.INVALID_CHALLENGE, "invalid_challenge")
    for method in (Method.META, Method.FILE, Method.DNS):
        try:
            return await verify_ownership(
                domain, token, method, lookup=lookup, http=http, base_url=base_url, now=now
            )
        except OwnershipError:
            continue
    challenge = Challenge(domain=domain, token=token, expires_at=0)
    raise OwnershipError(
        errors.PROOF_NOT_FOUND.format(domain=domain, url=challenge.file_url), "proof_not_found"
    )
