# Changelog

All notable changes to Vigilo are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-11-26

First public release: a passive website security check-up.

### Added

- **Checks**: TLS (certificate, expiry, TLS 1.0/1.1 refused and TLS 1.2/1.3 offered per
  BSI TR-03116-4, HTTP to HTTPS redirect), security headers, exposed sensitive files
  (status and size only, never the content), email security (SPF with nested lookups,
  DMARC, DKIM), platform detection with WordPress core and plugin updates, privacy and
  legal basics (not graded).
- **Report**: plain-language explanation of every result, observed value, copy-ready fixes
  for Apache, Nginx, Cloudflare and WordPress, letter grade from A to F with its scale.
- **Web interface** in English, French, German and Arabic (right-to-left), live scan log
  over Server-Sent Events, WCAG 2.1 AA target.
- **Signed PDF reports** in the reader's language, including right-to-left Arabic.
- **CLI** (`vigilo scan`, `--json`, `--markdown`, `--lang`, `--fail-under` for CI) and **HTTP API**.
- **GitHub Action** (`uses: daruilem/Vigilo@v0.1.0`): grade and fixes in the job summary,
  `score` and `grade` outputs, optional `fail-under` threshold.
- **Hardening**: SSRF and DNS rebinding protection, per-client and per-target rate limits,
  scan time and size limits, strict nonce-based CSP, hardened containers.
- **Domain ownership verification** (DNS TXT record or `.well-known` file), groundwork for
  the upcoming verified active scan. Hidden in the interface unless
  `NEXT_PUBLIC_VIGILO_ACTIVE_SCAN=1`.
- **Supply chain**: Dependabot, CodeQL, container images on GitHub Container Registry
  signed with Sigstore, with SBOM and build provenance.

[Unreleased]: https://github.com/daruilem/Vigilo/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/daruilem/Vigilo/releases/tag/v0.1.0
