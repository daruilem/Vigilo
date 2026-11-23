"""Reader-facing content: plain-language headlines, fixes per hosting, follow-up advice.

Kept apart from detection logic so the wording can be reviewed, or translated later,
without touching the checks. `{domain}` in a fix is replaced with the scanned domain.
"""

from __future__ import annotations

from vigilo.models import Finding, Fix, Platform, Status

A, N, C, W = Platform.APACHE, Platform.NGINX, Platform.CLOUDFLARE, Platform.WORDPRESS

HTACCESS = "Add this to the .htaccess file at the root of your site:"
WP_HTACCESS = "Most WordPress hosts run Apache or LiteSpeed. " + HTACCESS
NGINX_SERVER = "Add this inside the server { } block of your site, then reload Nginx:"
CF_TRANSFORM = (
    "Rules, then Transform Rules, then Modify Response Header. Create a rule for all "
    "requests that does this:"
)

# --- headlines ---------------------------------------------------------------------------

HEADLINES: dict[str, dict[Status, str]] = {
    "tls.certificate": {
        Status.FAIL: "Browsers do not trust your certificate",
        Status.PASS: "Certificate is valid",
    },
    "tls.certificate-expiry": {
        Status.FAIL: "Your certificate is about to expire",
        Status.WARN: "Your certificate expires within a month",
        Status.PASS: "Certificate is not close to expiry",
    },
    "tls.legacy-protocols": {
        Status.FAIL: "Your server still accepts obsolete encryption",
        Status.PASS: "Obsolete TLS versions are refused",
        Status.INFO: "Obsolete TLS versions could not be tested",
    },
    "tls.modern-protocols": {
        Status.FAIL: "Your server does not offer modern encryption",
        Status.WARN: "TLS 1.3 is not offered",
        Status.PASS: "TLS 1.3 is supported",
    },
    "tls.https-redirect": {
        Status.FAIL: "Visitors are not sent to the secure version of your site",
        Status.PASS: "Visitors are sent to the secure version",
        Status.INFO: "The site does not answer on plain HTTP",
    },
    "headers.hsts": {
        Status.FAIL: "Browsers are not told to always use HTTPS",
        Status.WARN: "HTTPS is enforced for a short time only",
        Status.PASS: "Browsers are told to always use HTTPS",
    },
    "headers.csp": {
        Status.FAIL: "Nothing limits what your pages can load",
        Status.WARN: "Your content policy still allows risky scripts",
        Status.PASS: "A content policy limits what your pages can load",
    },
    "headers.clickjacking": {
        Status.FAIL: "Other sites can show your pages inside a hidden frame",
        Status.PASS: "Other sites cannot frame your pages",
    },
    "headers.nosniff": {
        Status.FAIL: "Browsers may guess the type of files on your site",
        Status.PASS: "File types cannot be guessed",
    },
    "headers.referrer-policy": {
        Status.FAIL: "Your site does not control what it shares about visited pages",
        Status.WARN: "Your site shares full page addresses with other sites",
        Status.PASS: "Referrer policy is set",
    },
    "headers.permissions-policy": {
        Status.FAIL: "Camera, microphone and location are not restricted",
        Status.PASS: "Sensitive browser features are restricted",
    },
    "headers.server-disclosure": {
        Status.WARN: "Your server shows its exact software versions",
        Status.PASS: "Software versions are hidden",
    },
    "headers.unavailable": {Status.INFO: "Security headers could not be read"},
    "files.git": {Status.FAIL: "Your Git folder can be downloaded by anyone"},
    "files.env": {Status.FAIL: "Your secret settings file (.env) can be downloaded"},
    "files.backup": {Status.FAIL: "Backup files can be downloaded by anyone"},
    "files.none": {Status.PASS: "No sensitive files found"},
    "email.spf": {
        Status.FAIL: "Anyone can send emails pretending to be your domain",
        Status.WARN: "Your email sender list (SPF) does not block fake senders",
        Status.PASS: "Your domain lists who may send its emails (SPF)",
    },
    "email.dmarc": {
        Status.FAIL: "Fake emails in your name are not rejected",
        Status.WARN: "Fake emails in your name are reported but still delivered",
        Status.PASS: "DMARC protects your domain against fake emails",
    },
    "email.dkim": {
        Status.PASS: "Your emails can be signed (DKIM)",
        Status.INFO: "No email signature key (DKIM) found under common names",
    },
    "privacy.google-fonts": {
        Status.WARN: "Your site sends visitors' IP addresses to Google (Google Fonts)",
        Status.PASS: "Fonts are not loaded from Google",
    },
    "privacy.trackers": {
        Status.WARN: "Trackers load before visitors can agree",
        Status.PASS: "No trackers found in the page",
    },
    "legal.privacy-policy": {
        Status.WARN: "No privacy policy link on the home page",
        Status.PASS: "Privacy policy is linked",
    },
    "legal.impressum": {
        Status.FAIL: "No Impressum link on the home page",
        Status.PASS: "Impressum is linked",
    },
    "legal.mentions-legales": {
        Status.FAIL: "No legal notice (mentions légales) on the home page",
        Status.PASS: "Legal notice (mentions légales) is linked",
    },
}

# --- fixes -------------------------------------------------------------------------------


def _header_fixes(name: str, value: str) -> dict[Platform, Fix]:
    return {
        A: Fix(intro=HTACCESS, code=f'Header always set {name} "{value}"'),
        N: Fix(intro=NGINX_SERVER, code=f'add_header {name} "{value}" always;'),
        C: Fix(intro=CF_TRANSFORM, code=f"Set static   {name} = {value}"),
        W: Fix(intro=WP_HTACCESS, code=f'Header always set {name} "{value}"'),
    }


HSTS_VALUE = "max-age=31536000; includeSubDomains"
CSP_START = "default-src 'self'; img-src 'self' data:; frame-ancestors 'self'"
REDIRECT_APACHE = (
    "RewriteEngine On\nRewriteCond %{HTTPS} off\n"
    "RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]"
)
TLS_APACHE = "SSLProtocol -all +TLSv1.2 +TLSv1.3"
TLS_NGINX = "ssl_protocols TLSv1.2 TLSv1.3;"
BACKUP_PATTERN = r"\.(zip|sql|bak|tar|gz)$"

FIXES: dict[str, dict[Platform, Fix]] = {
    "tls.certificate": {
        A: Fix(
            intro="Get a free certificate from Let's Encrypt with Certbot. It also renews it automatically:",
            code="sudo certbot --apache -d {domain} -d www.{domain}",
        ),
        N: Fix(
            intro="Get a free certificate from Let's Encrypt with Certbot. It also renews it automatically:",
            code="sudo certbot --nginx -d {domain} -d www.{domain}",
        ),
        C: Fix(
            intro="SSL/TLS, then Overview. Choose this mode, and install a Cloudflare origin certificate on your server:",
            code="SSL/TLS encryption mode: Full (strict)",
        ),
        W: Fix(
            intro="Most hosts offer free certificates. In your hosting panel, look for SSL or Let's Encrypt and enable it for:",
            code="{domain}\nwww.{domain}",
        ),
    },
    "tls.certificate-expiry": {
        A: Fix(
            intro="Renew now, then check that automatic renewal works:",
            code="sudo certbot renew\nsudo certbot renew --dry-run",
        ),
        N: Fix(
            intro="Renew now, then check that automatic renewal works:",
            code="sudo certbot renew\nsudo certbot renew --dry-run",
        ),
        C: Fix(
            intro="Edge certificates renew by themselves. If the certificate on your server expires, create a new one here:",
            code="SSL/TLS > Origin Server > Create Certificate",
        ),
        W: Fix(
            intro="Ask your host to renew the certificate and to turn on automatic renewal for:",
            code="{domain}\nwww.{domain}",
        ),
    },
    "tls.legacy-protocols": {
        A: Fix(
            intro="In the SSL configuration of Apache (often ssl.conf), then restart Apache:",
            code=TLS_APACHE,
        ),
        N: Fix(intro="In the http { } or server { } block, then reload Nginx:", code=TLS_NGINX),
        C: Fix(intro="SSL/TLS, then Edge Certificates. Set:", code="Minimum TLS Version: TLS 1.2"),
        W: Fix(
            intro="This is a server setting. Ask your host to disable TLS 1.0 and TLS 1.1 for:",
            code="{domain}",
        ),
    },
    "tls.modern-protocols": {
        A: Fix(
            intro="In the SSL configuration of Apache (needs OpenSSL 1.1.1 or newer), then restart Apache:",
            code=TLS_APACHE,
        ),
        N: Fix(intro="In the http { } or server { } block, then reload Nginx:", code=TLS_NGINX),
        C: Fix(intro="SSL/TLS, then Edge Certificates. Switch on:", code="TLS 1.3: On"),
        W: Fix(
            intro="This is a server setting. Ask your host to enable TLS 1.2 and TLS 1.3 for:",
            code="{domain}",
        ),
    },
    "tls.https-redirect": {
        A: Fix(intro="Add this to .htaccess, above any other rules:", code=REDIRECT_APACHE),
        N: Fix(
            intro="Replace the server block that listens on port 80 with:",
            code=(
                "server {\n    listen 80;\n    server_name {domain} www.{domain};\n"
                "    return 301 https://$host$request_uri;\n}"
            ),
        ),
        C: Fix(intro="SSL/TLS, then Edge Certificates. Switch on:", code="Always Use HTTPS: On"),
        W: Fix(
            intro="In Settings, then General, write both addresses with https://. Then add this to .htaccess:",
            code=REDIRECT_APACHE,
        ),
    },
    "headers.hsts": {
        **_header_fixes("Strict-Transport-Security", HSTS_VALUE),
        C: Fix(
            intro="SSL/TLS, then Edge Certificates, then HTTP Strict Transport Security (HSTS). Enable it with:",
            code="Max-Age: 12 months\nInclude subdomains: On\nPreload: Off",
        ),
    },
    "headers.csp": {
        A: Fix(
            intro=(
                "Start in report-only mode: nothing is blocked, the browser console lists what "
                "would be. Add this to .htaccess:"
            ),
            code=f'Header always set Content-Security-Policy-Report-Only "{CSP_START}"',
        ),
        N: Fix(
            intro=(
                "Start in report-only mode: nothing is blocked, the browser console lists what "
                "would be. Add this inside the server { } block:"
            ),
            code=f'add_header Content-Security-Policy-Report-Only "{CSP_START}" always;',
        ),
        C: Fix(
            intro=CF_TRANSFORM,
            code=f"Set static   Content-Security-Policy-Report-Only = {CSP_START}",
        ),
        W: Fix(
            intro=(
                "Themes and plugins load many outside resources, so start in report-only mode. "
                "Add this to .htaccess:"
            ),
            code=f'Header always set Content-Security-Policy-Report-Only "{CSP_START}"',
        ),
    },
    "headers.clickjacking": _header_fixes("X-Frame-Options", "SAMEORIGIN"),
    "headers.nosniff": _header_fixes("X-Content-Type-Options", "nosniff"),
    "headers.referrer-policy": _header_fixes("Referrer-Policy", "strict-origin-when-cross-origin"),
    "headers.permissions-policy": _header_fixes(
        "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
    ),
    "headers.server-disclosure": {
        A: Fix(
            intro="In the main Apache configuration (not .htaccess), then restart Apache:",
            code="ServerTokens Prod\nServerSignature Off\n\n# in php.ini\nexpose_php = Off",
        ),
        N: Fix(
            intro="In the http { } block, then reload Nginx:",
            code="server_tokens off;\n\n# in php.ini\nexpose_php = Off",
        ),
        C: Fix(intro=CF_TRANSFORM, code="Remove   X-Powered-By"),
        W: Fix(
            intro="On shared hosting, ask your host to hide versions. You can already remove the PHP one in .htaccess:",
            code="Header unset X-Powered-By",
        ),
    },
    "files.git": {
        A: Fix(
            intro="Delete the .git folder from the server, then add this to .htaccess so it is never served again:",
            code=r"RedirectMatch 404 /\.git",
        ),
        N: Fix(
            intro="Delete the .git folder from the server, then add this inside the server { } block:",
            code="location ~ /\\.git {\n    return 404;\n}",
        ),
        C: Fix(
            intro="Security, then WAF, then Custom rules. Create a rule with this expression and the action Block:",
            code='(http.request.uri.path contains "/.git")',
        ),
        W: Fix(
            intro="Ask your host to delete the .git folder, or remove it with their file manager. Then add this to .htaccess:",
            code=r"RedirectMatch 404 /\.git",
        ),
    },
    "files.env": {
        A: Fix(
            intro="Move the .env file outside the public folder. Until then, block it in .htaccess:",
            code='<Files ".env">\n    Require all denied\n</Files>',
        ),
        N: Fix(
            intro="Move the .env file outside the public folder. Until then, add this inside the server { } block:",
            code="location ~ /\\.env {\n    return 404;\n}",
        ),
        C: Fix(
            intro="Security, then WAF, then Custom rules. Create a rule with this expression and the action Block:",
            code='(http.request.uri.path contains "/.env")',
        ),
        W: Fix(
            intro="Ask your host to move the file outside the public folder. Until then, add this to .htaccess:",
            code='<Files ".env">\n    Require all denied\n</Files>',
        ),
    },
    "files.backup": {
        A: Fix(
            intro="Delete these files and keep backups outside the website. If your site offers no such downloads, also add to .htaccess:",
            code=f'<FilesMatch "{BACKUP_PATTERN}">\n    Require all denied\n</FilesMatch>',
        ),
        N: Fix(
            intro="Delete these files and keep backups outside the website. If your site offers no such downloads, also add:",
            code=f"location ~* {BACKUP_PATTERN} {{\n    return 404;\n}}",
        ),
        C: Fix(
            intro="Delete the files first. Then, in Security, WAF, Custom rules, block this expression:",
            code=(
                '(ends_with(http.request.uri.path, ".sql") or '
                'ends_with(http.request.uri.path, ".bak"))'
            ),
        ),
        W: Fix(
            intro="Backup plugins sometimes leave archives in the site folder. Delete them, store backups elsewhere, and add to .htaccess:",
            code=f'<FilesMatch "{BACKUP_PATTERN}">\n    Require all denied\n</FilesMatch>',
        ),
    },
}

FOLLOW_UPS: dict[str, str] = {
    "headers.hsts": "only turn this on once every page and subdomain works over HTTPS.",
    "headers.csp": "once the console shows no unexpected blocks, rename the header to Content-Security-Policy.",
    "files.git": "change every password or key that was ever stored in this code.",
    "files.env": "change every password and key in this file. Consider them public.",
    "files.backup": "if a database dump was exposed, change the passwords it contains.",
}


def enrich(finding: Finding, domain: str) -> Finding:
    """Attach the headline, fixes and follow-up that match this finding's result."""
    update: dict[str, object] = {}

    headlines = HEADLINES.get(finding.id, {})
    headline = headlines.get(finding.status)
    if headline is None and finding.status is Status.WARN:
        headline = headlines.get(Status.FAIL)
    if headline is not None and finding.headline is None:
        update["headline"] = headline

    if finding.status in (Status.FAIL, Status.WARN):
        fixes = FIXES.get(finding.id)
        if fixes and not finding.fixes:
            update["fixes"] = {
                platform: Fix(
                    intro=fix.intro.replace("{domain}", domain),
                    code=fix.code.replace("{domain}", domain),
                )
                for platform, fix in fixes.items()
            }
        if finding.id in FOLLOW_UPS:
            update["follow_up"] = FOLLOW_UPS[finding.id]

    return finding.model_copy(update=update) if update else finding
