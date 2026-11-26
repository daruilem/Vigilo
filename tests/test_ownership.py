import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from vigilo import api, errors
from vigilo.i18n import CATALOGS, translate
from vigilo.ownership import (
    CHALLENGE_LIFETIME,
    PASS_LIFETIME,
    Method,
    OwnershipError,
    check_challenge,
    check_pass,
    create_challenge,
    issue_pass,
    verify_any,
    verify_ownership,
)

NOW = 1_800_000_000.0
DOMAIN = "shop.example"


# --- Signed codes ----------------------------------------------------------------------


def test_challenge_is_valid_for_its_domain_until_it_expires():
    challenge = create_challenge(DOMAIN, now=NOW)
    assert challenge.expires_at == NOW + CHALLENGE_LIFETIME
    assert check_challenge(DOMAIN, challenge.token, now=NOW)
    assert check_challenge(DOMAIN, challenge.token, now=NOW + CHALLENGE_LIFETIME - 1)
    assert not check_challenge(DOMAIN, challenge.token, now=NOW + CHALLENGE_LIFETIME)


def test_challenge_is_bound_to_the_exact_host_name():
    token = create_challenge(DOMAIN, now=NOW).token
    assert not check_challenge("other.example", token, now=NOW)
    assert not check_challenge("www.shop.example", token, now=NOW)


def test_each_challenge_is_different():
    assert create_challenge(DOMAIN).token != create_challenge(DOMAIN).token


@pytest.mark.parametrize(
    "token",
    ["", "abc", "a.b.c", "a.1.b.c", "nonce.notanumber.mac", "nonce.1800000000.mac"],
)
def test_malformed_or_forged_challenges_are_refused(token):
    assert not check_challenge(DOMAIN, token, now=NOW)


def test_extending_the_expiry_breaks_the_signature():
    nonce, expires, mac = create_challenge(DOMAIN, now=NOW).token.split(".")
    longer = f"{nonce}.{int(expires) + 86400}.{mac}"
    assert not check_challenge(DOMAIN, longer, now=NOW)


def test_challenge_is_short_enough_for_a_txt_record():
    challenge = create_challenge(DOMAIN)
    assert len(challenge.dns_value) < 255  # one TXT character-string
    assert challenge.dns_name == "_vigilo.shop.example"
    nonce = challenge.token.split(".")[0]
    assert challenge.file_name == f"vigilo-{nonce}.txt"
    assert challenge.file_url == f"https://shop.example/vigilo-{nonce}.txt"
    assert challenge.meta_tag == f'<meta name="vigilo-verification" content="{challenge.token}">'


def test_pass_is_valid_for_its_domain_until_it_expires():
    proof = issue_pass(DOMAIN, Method.DNS, now=NOW)
    assert proof.expires_at == NOW + PASS_LIFETIME
    assert check_pass(DOMAIN, proof.token, now=NOW) is Method.DNS
    assert check_pass("other.example", proof.token, now=NOW) is None
    assert check_pass(DOMAIN, proof.token, now=NOW + PASS_LIFETIME) is None


def test_challenge_and_pass_cannot_be_swapped():
    challenge = create_challenge(DOMAIN, now=NOW)
    proof = issue_pass(DOMAIN, Method.FILE, now=NOW)
    assert check_pass(DOMAIN, challenge.token, now=NOW) is None
    assert not check_challenge(DOMAIN, proof.token, now=NOW)


def test_changing_the_method_of_a_pass_breaks_it():
    _, expires, mac = issue_pass(DOMAIN, Method.FILE, now=NOW).token.split(".")
    assert check_pass(DOMAIN, f"dns.{expires}.{mac}", now=NOW) is None


# --- Verification ----------------------------------------------------------------------


def run(coro):
    return asyncio.run(coro)


def fake_dns(records):
    async def lookup(name):
        return records.get(name, [])

    return lookup


def test_dns_proof():
    challenge = create_challenge(DOMAIN, now=NOW)
    lookup = fake_dns({"_vigilo.shop.example": ["something else", challenge.dns_value]})
    proof = run(verify_ownership(DOMAIN, challenge.token, Method.DNS, lookup=lookup, now=NOW))
    assert proof.domain == DOMAIN
    assert check_pass(DOMAIN, proof.token, now=NOW) is Method.DNS


def test_missing_dns_record():
    challenge = create_challenge(DOMAIN, now=NOW)
    with pytest.raises(OwnershipError) as error:
        run(verify_ownership(DOMAIN, challenge.token, Method.DNS, lookup=fake_dns({}), now=NOW))
    assert error.value.code == "record_not_found"
    assert "_vigilo.shop.example" in error.value.message


def test_dns_record_with_an_old_code():
    challenge = create_challenge(DOMAIN, now=NOW)
    old = create_challenge(DOMAIN, now=NOW)
    lookup = fake_dns({"_vigilo.shop.example": [old.dns_value]})
    with pytest.raises(OwnershipError) as error:
        run(verify_ownership(DOMAIN, challenge.token, Method.DNS, lookup=lookup, now=NOW))
    assert error.value.code == "record_mismatch"


def test_record_on_the_bare_domain_does_not_count():
    challenge = create_challenge(DOMAIN, now=NOW)
    lookup = fake_dns({DOMAIN: [challenge.dns_value]})
    with pytest.raises(OwnershipError):
        run(verify_ownership(DOMAIN, challenge.token, Method.DNS, lookup=lookup, now=NOW))


def file_check(handler, token, domain=DOMAIN, method=Method.FILE):
    async def go():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler), follow_redirects=True
        ) as http:
            return await verify_ownership(domain, token, method, http=http, now=NOW)

    return run(go())


def page(head="", body=""):
    return f"<html><head><title>Shop</title>{head}</head><body>{body}</body></html>"


# --- HTML tag ---------------------------------------------------------------------------


def test_meta_tag_proof():
    challenge = create_challenge(DOMAIN, now=NOW)
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, text=page(head=challenge.meta_tag))

    proof = file_check(handler, challenge.token, method=Method.META)
    assert seen == ["https://shop.example/"]
    assert check_pass(DOMAIN, proof.token, now=NOW) is Method.META


def test_meta_tag_in_the_body_does_not_count():
    # Visitors can sometimes add content to a page (comments, reviews), never to its head.
    challenge = create_challenge(DOMAIN, now=NOW)
    html = page(body=f"<p>Nice shop!</p>{challenge.meta_tag}")
    with pytest.raises(OwnershipError) as error:
        file_check(lambda r: httpx.Response(200, text=html), challenge.token, method=Method.META)
    assert error.value.code == "meta_not_found"


def test_meta_tag_with_another_code():
    challenge = create_challenge(DOMAIN, now=NOW)
    old = create_challenge(DOMAIN, now=NOW).meta_tag
    with pytest.raises(OwnershipError) as error:
        file_check(
            lambda r: httpx.Response(200, text=page(head=old)), challenge.token, method=Method.META
        )
    assert error.value.code == "meta_mismatch"


def test_meta_tag_on_a_page_that_redirects_to_www_proves_nothing():
    challenge = create_challenge(DOMAIN, now=NOW)

    def handler(request):
        if request.url.host == DOMAIN:
            return httpx.Response(301, headers={"Location": "https://www.shop.example/"})
        return httpx.Response(200, text=page(head=challenge.meta_tag))

    with pytest.raises(OwnershipError) as error:
        file_check(handler, challenge.token, method=Method.META)
    assert error.value.code == "page_redirected"
    assert "www.shop.example" in error.value.message


# --- Automatic: every method ------------------------------------------------------------


def auto_check(handler, token, records=None):
    async def go():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler), follow_redirects=True
        ) as http:
            return await verify_any(
                DOMAIN, token, http=http, lookup=fake_dns(records or {}), now=NOW
            )

    return run(go())


def test_auto_accepts_whichever_method_was_used():
    challenge = create_challenge(DOMAIN, now=NOW)

    def only_the_file(request):
        if request.url.path == f"/{challenge.file_name}":
            return httpx.Response(200, text=challenge.token)
        return httpx.Response(200, text=page())

    assert auto_check(only_the_file, challenge.token).method is Method.FILE

    nothing_on_the_site = lambda request: httpx.Response(404)  # noqa: E731
    by_dns = auto_check(
        nothing_on_the_site, challenge.token, {challenge.dns_name: [challenge.dns_value]}
    )
    assert by_dns.method is Method.DNS


def test_auto_says_when_the_code_is_not_published_yet():
    challenge = create_challenge(DOMAIN, now=NOW)
    with pytest.raises(OwnershipError) as error:
        auto_check(lambda request: httpx.Response(200, text=page()), challenge.token)
    assert error.value.code == "proof_not_found"
    assert challenge.file_url in error.value.message


def test_auto_refuses_a_forged_code_without_any_network_activity():
    def handler(request):
        raise AssertionError("the site must not be contacted")

    forged = create_challenge("other.example", now=NOW).token
    with pytest.raises(OwnershipError) as error:
        auto_check(handler, forged)
    assert error.value.code == "invalid_challenge"


def test_file_proof():
    challenge = create_challenge(DOMAIN, now=NOW)
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, text=challenge.token + "\n")

    proof = file_check(handler, challenge.token)
    assert seen == [challenge.file_url]
    assert check_pass(DOMAIN, proof.token, now=NOW) is Method.FILE


@pytest.mark.parametrize(
    ("response", "code"),
    [
        (httpx.Response(404, text="Not found"), "file_not_found"),
        (httpx.Response(200, text="wrong code"), "file_mismatch"),
        (httpx.Response(200, text=""), "file_mismatch"),
    ],
)
def test_file_problems(response, code):
    challenge = create_challenge(DOMAIN, now=NOW)
    with pytest.raises(OwnershipError) as error:
        file_check(lambda request: response, challenge.token)
    assert error.value.code == code


def test_file_redirected_to_another_host_does_not_prove_anything():
    challenge = create_challenge(DOMAIN, now=NOW)

    def handler(request):
        if request.url.host == DOMAIN:
            return httpx.Response(302, headers={"Location": "https://attacker.example/code.txt"})
        return httpx.Response(200, text=challenge.token)

    with pytest.raises(OwnershipError) as error:
        file_check(handler, challenge.token)
    assert error.value.code == "file_redirected"


def test_redirect_on_the_same_host_is_followed():
    challenge = create_challenge(DOMAIN, now=NOW)

    def handler(request):
        if request.url.path == f"/{challenge.file_name}":
            return httpx.Response(301, headers={"Location": "/files/code.txt"})
        return httpx.Response(200, text=challenge.token)

    assert file_check(handler, challenge.token).domain == DOMAIN


def test_unreachable_site():
    challenge = create_challenge(DOMAIN, now=NOW)

    def handler(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(OwnershipError) as error:
        file_check(handler, challenge.token)
    assert error.value.code == "unreachable"


def test_huge_file_is_not_read_entirely():
    challenge = create_challenge(DOMAIN, now=NOW)
    body = challenge.token + "x" * 10_000_000
    with pytest.raises(OwnershipError) as error:
        file_check(lambda request: httpx.Response(200, text=body), challenge.token)
    assert error.value.code == "file_mismatch"


def test_no_network_activity_without_a_valid_code():
    def handler(request):
        raise AssertionError("the site must not be contacted")

    async def lookup(name):
        raise AssertionError("DNS must not be queried")

    forged = create_challenge("other.example", now=NOW).token
    for method in Method:
        with pytest.raises(OwnershipError) as error:
            run(verify_ownership(DOMAIN, forged, method, lookup=lookup, now=NOW))
        assert error.value.code == "invalid_challenge"
    with pytest.raises(OwnershipError):
        file_check(handler, forged)


# --- Translations ----------------------------------------------------------------------


@pytest.mark.parametrize("language", sorted(CATALOGS))
def test_ownership_messages_are_translated(language):
    url = "https://shop.example/vigilo-abc.txt"
    messages = [
        errors.META_NOT_FOUND.format(domain=DOMAIN),
        errors.META_MISMATCH.format(domain=DOMAIN),
        errors.PAGE_REDIRECTED.format(domain=DOMAIN, other="www.shop.example"),
        errors.PROOF_NOT_FOUND.format(domain=DOMAIN, url=url),
        errors.HOSTED_PLATFORM.format(platform="Shopify"),
        errors.INVALID_CHALLENGE,
        errors.OWNERSHIP_EXPIRED,
        errors.VERIFICATIONS_LIMITED,
        errors.DNS_UNAVAILABLE,
        errors.RECORD_NOT_FOUND.format(name="_vigilo.shop.example"),
        errors.RECORD_MISMATCH.format(name="_vigilo.shop.example"),
        errors.FILE_NOT_FOUND.format(url=url),
        errors.FILE_MISMATCH.format(url=url),
        errors.FILE_REDIRECTED.format(url=url, hostname=DOMAIN),
    ]
    untranslated = [m for m in messages if translate(m, language) == m]
    assert untranslated == []
    translated = translate(errors.FILE_REDIRECTED.format(url=url, hostname=DOMAIN), language)
    assert url in translated and DOMAIN in translated


# --- API -------------------------------------------------------------------------------

client = TestClient(api.app)


@pytest.fixture(autouse=True)
def reset_limits(monkeypatch):
    async def not_hosted(domain):
        return None

    monkeypatch.setattr(api, "_hosted_platform", not_hosted)
    api.ownership_limiter.reset()
    yield
    api.ownership_limiter.reset()


def test_api_challenge():
    response = client.post("/api/v1/ownership/challenge", json={"target": "https://Shop.Example/a"})
    assert response.status_code == 200
    body = response.json()
    assert body["domain"] == DOMAIN
    assert body["dns"] == {
        "name": "_vigilo.shop.example",
        "type": "TXT",
        "value": "vigilo-verification=" + body["token"],
    }
    assert body["file"]["content"] == body["token"]
    assert body["file"]["url"] == f"https://shop.example/{body['file']['name']}"
    assert body["meta"]["tag"] == f'<meta name="vigilo-verification" content="{body["token"]}">'
    assert check_challenge(DOMAIN, body["token"])


@pytest.mark.parametrize(
    ("html", "refused"),
    [
        ('<script src="https://cdn.shopify.com/s/files/theme.js"></script>', True),
        ('<link href="/wp-content/themes/shop/style.css">', False),
    ],
)
def test_api_challenge_refuses_sites_on_hosted_platforms(monkeypatch, html, refused):
    monkeypatch.undo()  # use the real platform check
    api.ownership_limiter.reset()

    async def homepage(http, url, max_bytes=0):
        return httpx.Response(200, text=html, request=httpx.Request("GET", url))

    monkeypatch.setattr(api, "fetch_page", homepage)
    response = client.post("/api/v1/ownership/challenge", json={"target": DOMAIN})
    if refused:
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "hosted_platform"
        assert "Shopify" in response.json()["detail"]["message"]
    else:
        assert response.status_code == 200


def test_api_verify_auto(monkeypatch):
    calls = []

    async def fake_any(domain, token, **kwargs):
        calls.append(domain)
        return issue_pass(domain, Method.META)

    monkeypatch.setattr(api, "verify_any", fake_any)
    token = create_challenge(DOMAIN).token
    response = client.post("/api/v1/ownership/verify", json={"target": DOMAIN, "token": token})
    assert response.status_code == 200
    assert response.json()["method"] == "meta"
    assert calls == [DOMAIN]


def test_api_challenge_rejects_invalid_targets():
    response = client.post("/api/v1/ownership/challenge", json={"target": "10.0.0.1"})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_target"


def test_api_verify(monkeypatch):
    async def lookup(name):
        return [f"vigilo-verification={token}"] if name == "_vigilo.shop.example" else []

    async def verify_with_fake_dns(domain, token, method):
        return await verify_ownership(domain, token, method, lookup=lookup)

    monkeypatch.setattr(api, "verify_ownership", verify_with_fake_dns)
    token = create_challenge(DOMAIN).token
    response = client.post(
        "/api/v1/ownership/verify", json={"target": DOMAIN, "token": token, "method": "dns"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["method"] == "dns"
    assert check_pass(DOMAIN, body["ownership_pass"]) is Method.DNS


def test_api_verify_refuses_a_forged_code_in_the_requested_language():
    token = create_challenge("other.example").token
    response = client.post(
        "/api/v1/ownership/verify",
        json={"target": DOMAIN, "token": token, "method": "file", "lang": "de"},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "invalid_challenge"
    assert detail["message"] == translate(errors.INVALID_CHALLENGE, "de")


def test_api_verifications_are_rate_limited(monkeypatch):
    monkeypatch.setattr(api.ownership_limiter, "max_events", 2)
    for _ in range(2):
        client.post("/api/v1/ownership/challenge", json={"target": DOMAIN})
    response = client.post("/api/v1/ownership/challenge", json={"target": DOMAIN})
    assert response.status_code == 429
    assert response.json()["detail"]["message"] == errors.VERIFICATIONS_LIMITED
