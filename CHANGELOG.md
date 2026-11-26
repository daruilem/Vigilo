# Changelog

All notable changes to Vigilo are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **Verified active scan** (API, off by default): Nuclei web templates and the OWASP ZAP
  baseline in throwaway, locked-down Docker containers; proof of ownership checked again
  at launch; consent log; daily limits; background jobs followed over Server-Sent Events;
  separate grade, signed report.
- **Local lab** (`docker-compose.lab.yml`): OWASP Juice Shop as `juice.lab` on a network
  without internet access, and a lab mode limited to `.lab` and `.test` names.
- `vigilo prepare-active` installs a pinned version of the Nuclei templates.
- **Active scan in the web interface**: conditions to accept, live log, full-page active
  report with its own grade, PDF titled and signed off as an active scan, back to the
  check-up. Browser tests cover the whole flow with accessibility checks.

- **Easier proof of ownership**: an HTML tag method and a file at the site root join the
  DNS record; a ready-made message (email, WhatsApp, copy) for whoever runs the site;
  automatic checks of every method every 30 seconds; step-by-step guides per platform;
  the pending code is kept in the browser so the owner can come back later.
- Sites on hosted platforms (Shopify, Wix, Squarespace, Webflow) are not offered the
  active scan: it would test the platform's servers.

### Changed

- The ownership file moved from `/.well-known/vigilo-verification.txt` to
  `/vigilo-<id>.txt` at the root, easier to upload.

### Fixed

- Advice for active scan results pointed "below" to information shown above it.

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
- **Progress since the last check**: opt-in summary kept in the visitor's browser; the next
  check of the site shows what was fixed, what is new and the score change.
- **CLI** (`vigilo scan`, `--json`, `--markdown`, `--lang`, `--fail-under` for CI) and **HTTP API**.
- **GitHub Action** (`uses: daruilem/Vigilo@v0.1.0`): grade and fixes in the job summary,
  `score` and `grade` outputs, optional `fail-under` threshold.
- **Hardening**: SSRF and DNS rebinding protection, per-client and per-target rate limits,
  scan time and size limits, strict nonce-based CSP, hardened containers.
- **Domain ownership verification** (DNS TXT record or `.well-known` file), groundwork for
  the upcoming verified active scan. Hidden in the interface unless
  `NEXT_PUBLIC_VIGILO_ACTIVE_SCAN=1`.
- **Browser tests** (Playwright) with axe accessibility checks, desktop and mobile.
- **Supply chain**: Dependabot, CodeQL, container images on GitHub Container Registry
  signed with Sigstore, with SBOM and build provenance.

[Unreleased]: https://github.com/daruilem/Vigilo/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/daruilem/Vigilo/releases/tag/v0.1.0
