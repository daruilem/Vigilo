# Security Policy

## Reporting a vulnerability

Please do **not** open a public issue for security problems in Vigilo itself.
Use GitHub's private vulnerability reporting instead
(*Security* tab, then *Report a vulnerability*).

You can expect an acknowledgement within 7 days. Please include steps to reproduce
and the version you tested.

## Supported versions

Security fixes go into the latest release only.

| Version | Supported |
|---|---|
| 0.1.x | yes |

## Scope

Of particular interest:

- ways to make Vigilo reach internal or private addresses (SSRF, DNS rebinding,
  redirect tricks),
- ways to run active checks against a domain without proving ownership,
- injection into generated reports.

## Responsible use

Vigilo must only be used on websites you own or are authorised to test.
