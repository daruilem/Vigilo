import pytest

from vigilo.target import Target, TargetError, is_public_address, parse_target


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("example.com", Target("example.com")),
        ("  Example.COM  ", Target("example.com")),
        ("https://www.example.com/some/page?x=1", Target("www.example.com")),
        ("http://example.com", Target("example.com")),
        ("example.com.", Target("example.com")),
        ("https://example.com:8443", Target("example.com", 8443)),
        ("bücher.de", Target("xn--bcher-kva.de")),
    ],
)
def test_parse_valid_targets(raw, expected):
    assert parse_target(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "ftp://example.com",
        "localhost",
        "192.168.1.1",
        "https://[::1]/",
        "-bad-.com",
        "exa mple.com",
        "a" * 64 + ".com",
        "https://example.com:99999",
    ],
)
def test_parse_rejects_invalid_targets(raw):
    with pytest.raises(TargetError):
        parse_target(raw)


@pytest.mark.parametrize(
    ("address", "public"),
    [
        ("93.184.215.14", True),
        ("2606:2800:21f:cb07:6820:80da:af6b:8b2c", True),
        ("127.0.0.1", False),
        ("10.0.0.5", False),
        ("172.16.3.4", False),
        ("192.168.1.10", False),
        ("169.254.169.254", False),  # cloud metadata endpoint
        ("100.64.0.1", False),  # carrier-grade NAT
        ("::1", False),
        ("fe80::1%eth0", False),
        ("::ffff:127.0.0.1", False),
        ("224.0.0.1", False),
    ],
)
def test_is_public_address(address, public):
    assert is_public_address(address) is public


def test_target_urls():
    assert Target("example.com").https_url == "https://example.com/"
    assert Target("example.com", 8443).https_url == "https://example.com:8443/"
    assert Target("example.com").http_url == "http://example.com/"
