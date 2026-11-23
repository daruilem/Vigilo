from vigilo.checks.base import Check, ScanContext
from vigilo.checks.cms import CmsCheck
from vigilo.checks.email import EmailCheck
from vigilo.checks.files import FilesCheck
from vigilo.checks.headers import HeadersCheck
from vigilo.checks.privacy import PrivacyCheck
from vigilo.checks.tls import TlsCheck

ALL_CHECKS: list[Check] = [
    TlsCheck(),
    HeadersCheck(),
    FilesCheck(),
    EmailCheck(),
    CmsCheck(),
    PrivacyCheck(),
]

__all__ = [
    "ALL_CHECKS",
    "Check",
    "CmsCheck",
    "EmailCheck",
    "FilesCheck",
    "HeadersCheck",
    "PrivacyCheck",
    "ScanContext",
    "TlsCheck",
]
