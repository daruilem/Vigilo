"""Errors that stop a scan before a report can be produced.

Each error has a stable `code` for clients and a one-sentence message that says what
happened and what to do.
"""

from __future__ import annotations


class ScanError(Exception):
    code: str = "scan_error"

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


UNREACHABLE = (
    "We could not connect to this website. Check the address, or try again later if the "
    "site is down."
)
TIMEOUT = "The website took more than 10 seconds to answer. Try again in a few minutes."
TOO_MANY_REDIRECTS = (
    "The website keeps redirecting (more than 5 times in a row). Check its redirect "
    "settings, then try again."
)
NOT_AUTHORIZED = (
    "Please confirm that you run this website or have permission to check it, then try again."
)
RATE_LIMITED = "You have run many checks in a short time. Wait a few minutes, then try again."
TARGET_RATE_LIMITED = (
    "This website was checked several times in the last few minutes. Wait a few minutes "
    "before checking it again."
)
BUSY = "Vigilo is busy with other checks right now. Try again in a minute."
SCAN_TIMEOUT = "The check took too long and was stopped. Try again in a few minutes."
INTERNAL = "Something went wrong on our side. Please try again in a moment."
INVALID_REPORT = (
    "This report can no longer be turned into a PDF. Run the check again, then download it."
)
TOO_LARGE = "The request is too large."

# Domain ownership (before an active scan). Placeholders are filled with str.format.
INVALID_CHALLENGE = (
    "This verification code is not valid for this domain or has expired. Ask for a new "
    "code, then try again."
)
OWNERSHIP_EXPIRED = (
    "The proof of ownership for this domain is missing or has expired. Verify the domain "
    "again, then try again."
)
VERIFICATIONS_LIMITED = (
    "You have tried many verifications in a short time. Wait a few minutes, then try again."
)
DNS_UNAVAILABLE = (
    "We could not read the DNS records of this domain right now. Try again in a few minutes."
)
RECORD_NOT_FOUND = (
    "We did not find the TXT record {name}. DNS changes can take up to an hour to appear: "
    "wait a little, then try again."
)
RECORD_MISMATCH = (
    "The TXT record {name} exists but does not contain this code. Replace its value with "
    "the one shown, then try again."
)
FILE_NOT_FOUND = (
    "We could not find the file {url}. Check that it is online at exactly this address, "
    "then try again."
)
FILE_MISMATCH = (
    "The file {url} does not contain this code. Its content must be exactly the code "
    "shown, then try again."
)
FILE_REDIRECTED = (
    "The address {url} redirects to another site. The file must be served directly by {hostname}."
)
