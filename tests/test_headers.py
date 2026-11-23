from vigilo.checks.headers import evaluate_headers, unsafe_script_sources
from vigilo.models import Status

GOOD_HEADERS = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'self'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Server": "nginx",
}


def by_id(findings):
    return {f.id: f for f in findings}


def test_well_configured_site_passes_everything():
    findings = evaluate_headers(GOOD_HEADERS)
    assert all(f.status is Status.PASS for f in findings), [
        (f.id, f.status) for f in findings if f.status is not Status.PASS
    ]


def test_no_headers_fails_the_important_ones():
    results = by_id(evaluate_headers({}))
    for fid in (
        "headers.hsts",
        "headers.csp",
        "headers.clickjacking",
        "headers.nosniff",
        "headers.referrer-policy",
        "headers.permissions-policy",
    ):
        assert results[fid].status is Status.FAIL
        assert results[fid].recommendation


def test_header_names_are_case_insensitive():
    lower = {k.lower(): v for k, v in GOOD_HEADERS.items()}
    assert all(f.status is Status.PASS for f in evaluate_headers(lower))


def test_short_hsts_is_a_warning():
    headers = {**GOOD_HEADERS, "Strict-Transport-Security": "max-age=300"}
    hsts = by_id(evaluate_headers(headers))["headers.hsts"]
    assert hsts.status is Status.WARN
    assert hsts.evidence["max_age"] == 300


def test_csp_with_unsafe_inline_is_a_warning():
    headers = {**GOOD_HEADERS, "Content-Security-Policy": "script-src 'self' 'unsafe-inline'"}
    csp = by_id(evaluate_headers(headers))["headers.csp"]
    assert csp.status is Status.WARN
    assert csp.evidence["unsafe_keywords"] == ["'unsafe-inline'"]


def test_x_frame_options_alone_protects_against_clickjacking():
    headers = {**GOOD_HEADERS, "Content-Security-Policy": "default-src 'self'"}
    headers["X-Frame-Options"] = "SAMEORIGIN"
    assert by_id(evaluate_headers(headers))["headers.clickjacking"].status is Status.PASS


def test_invalid_x_frame_options_value_does_not_count():
    headers = {k: v for k, v in GOOD_HEADERS.items() if k != "Content-Security-Policy"}
    headers["X-Frame-Options"] = "ALLOW-FROM https://example.org"
    assert by_id(evaluate_headers(headers))["headers.clickjacking"].status is Status.FAIL


def test_weak_referrer_policy_is_a_warning():
    headers = {**GOOD_HEADERS, "Referrer-Policy": "unsafe-url"}
    assert by_id(evaluate_headers(headers))["headers.referrer-policy"].status is Status.WARN


def test_version_disclosure_is_reported():
    headers = {**GOOD_HEADERS, "Server": "Apache/2.4.41 (Ubuntu)", "X-Powered-By": "PHP/7.4.3"}
    finding = by_id(evaluate_headers(headers))["headers.server-disclosure"]
    assert finding.status is Status.WARN
    assert set(finding.evidence) == {"server", "x-powered-by"}


def test_unsafe_inline_in_style_src_only_is_not_reported():
    policy = "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'"
    headers = {**GOOD_HEADERS, "Content-Security-Policy": policy}
    assert by_id(evaluate_headers(headers))["headers.csp"].status is Status.PASS


def test_unsafe_inline_falls_back_to_default_src():
    headers = {**GOOD_HEADERS, "Content-Security-Policy": "default-src 'self' 'unsafe-inline'"}
    assert by_id(evaluate_headers(headers))["headers.csp"].status is Status.WARN


def test_unsafe_inline_is_ignored_when_a_nonce_is_present():
    policy = "script-src 'self' 'nonce-abc123' 'unsafe-inline'"
    assert unsafe_script_sources(policy) == []


def test_unsafe_eval_is_always_reported():
    assert unsafe_script_sources("script-src 'self' 'unsafe-eval'") == ["'unsafe-eval'"]
