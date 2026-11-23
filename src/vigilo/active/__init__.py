"""Verified active scan: test requests sent to a site whose owner proved control of it.

- `vigilo.ownership` checks the proof of ownership (required before anything here runs),
- `parsers` reads the tools' output, keeping only in-scope results and no site data,
- `findings` turns those results into plain-language, translated report findings.
"""

from vigilo.active.findings import to_findings
from vigilo.active.parsers import ToolResult, parse_nuclei, parse_zap

__all__ = ["ToolResult", "parse_nuclei", "parse_zap", "to_findings"]
