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
