"""Proof of domain ownership, required before any active scan.

A passive check only reads what a website shows every visitor, so a confirmation box is
enough. An active scan sends test requests, and running one against a site without the
owner's permission is a criminal offence in most countries (for example section 202c of
the German Criminal Code). Vigilo therefore asks for a proof that only someone who
controls the domain can give:

1. DNS: a TXT record `_vigilo.<domain>` with the value `vigilo-verification=<code>`, or
2. File: `https://<domain>/.well-known/vigilo-verification.txt` containing the code.

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

import dns.asyncresolver
import dns.exception
import dns.resolver
import httpx

from vigilo import errors
from vigilo.errors import ScanError
from vigilo.net import fetch_page, make_client
from vigilo.signing import tag

CHALLENGE_LIFETIME = 24 * 3600
PASS_LIFETIME = 24 * 3600
RECORD_LABEL = "_vigilo"
RECORD_PREFIX = "vigilo-verification="
FILE_PATH = "/.well-known/vigilo-verification.txt"
MAX_FILE_BYTES = 1024
DNS_TIMEOUT = 5.0

_CHALLENGE = "ownership-challenge"
_PROOF = "ownership-proof"
_CHALLENGE_TAG_LENGTH = 32  # 128 bits: plenty for a code that lives 24 hours, and short to copy


class Method(str, Enum):
    DNS = "dns"
    FILE = "file"


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
    def file_url(self) -> str:
        return f"https://{self.domain}{FILE_PATH}"


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


async def _verify_file(challenge: Challenge, http: httpx.AsyncClient) -> None:
    url = challenge.file_url
    try:
        response = await fetch_page(http, url, MAX_FILE_BYTES)
    except httpx.TooManyRedirects as exc:
        raise OwnershipError(errors.TOO_MANY_REDIRECTS, "too_many_redirects") from exc
    except httpx.TimeoutException as exc:
        raise OwnershipError(errors.TIMEOUT, "timeout") from exc
    except httpx.TransportError as exc:
        raise OwnershipError(errors.UNREACHABLE, "unreachable") from exc

    # A redirect to another host would prove control of that host, not of this domain.
    if response.request.url.host != challenge.domain:
        raise OwnershipError(
            errors.FILE_REDIRECTED.format(url=url, hostname=challenge.domain), "file_redirected"
        )
    if response.status_code != 200:
        raise OwnershipError(errors.FILE_NOT_FOUND.format(url=url), "file_not_found")
    content = response.content.decode("utf-8", "replace").strip()
    if not hmac.compare_digest(content, challenge.token):
        raise OwnershipError(errors.FILE_MISMATCH.format(url=url), "file_mismatch")


async def verify_ownership(
    domain: str,
    token: str,
    method: Method,
    *,
    lookup: TxtLookup = lookup_txt,
    http: httpx.AsyncClient | None = None,
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
    elif http is not None:
        await _verify_file(challenge, http)
    else:
        async with make_client() as client:
            await _verify_file(challenge, client)
    return issue_pass(domain, method, now=now)
