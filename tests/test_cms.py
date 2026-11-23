import pytest

from vigilo.checks.cms import detect, evaluate, is_outdated, plugin_versions
from vigilo.models import Platform, Status


def by_id(findings):
    return {f.id: f for f in findings}


WP_PAGE = """<html><head><meta name="generator" content="WordPress 6.4.2" />
<link rel="stylesheet" href="/wp-content/themes/x/style.css"></head></html>"""


def test_detects_wordpress_and_its_version():
    detection = detect(WP_PAGE)
    assert detection.cms.name == "WordPress"
    assert detection.version == "6.4.2"


def test_detects_wordpress_without_version():
    detection = detect('<html><script src="/wp-includes/js/jquery.js"></script></html>')
    assert detection.cms.name == "WordPress"
    assert detection.version is None


def test_detects_hosted_platforms():
    assert detect('<img src="https://cdn.shopify.com/s/files/logo.png">').cms.name == "Shopify"


def test_drupal_from_header():
    assert detect("<html></html>", "Drupal 10 (https://www.drupal.org)").cms.name == "Drupal"


def test_nothing_detected():
    assert detect("<html><body>Hello</body></html>") is None


@pytest.mark.parametrize(
    ("version", "latest", "outdated"),
    [
        ("6.4.2", "6.7.1", True),
        ("6.7", "6.7.1", True),
        ("6.7.1", "6.7.1", False),
        ("6.8", "6.7.1", False),
    ],
)
def test_is_outdated(version, latest, outdated):
    assert is_outdated(version, latest) is outdated


def test_outdated_wordpress_is_high():
    results = by_id(evaluate(detect(WP_PAGE), "6.7.1"))
    outdated = results["cms.wordpress-outdated"]
    assert outdated.status is Status.FAIL
    assert "6.7.1" in outdated.fixes[Platform.WORDPRESS].code
    assert results["cms.version-disclosed"].status is Status.WARN
    assert results["cms.detected"].headline == "Built with WordPress"


def test_up_to_date_wordpress_passes():
    results = by_id(evaluate(detect(WP_PAGE), "6.4.2"))
    assert results["cms.wordpress-outdated"].status is Status.PASS


def test_unknown_latest_version_skips_the_update_check():
    assert "cms.wordpress-outdated" not in by_id(evaluate(detect(WP_PAGE), None))


def test_hosted_platform_has_no_version_warning():
    results = by_id(evaluate(detect('<script src="https://static.wixstatic.com/x.js">')))
    assert set(results) == {"cms.detected"}
    assert "installs security updates" in results["cms.detected"].description


PLUGIN_PAGE = """<meta name="generator" content="WordPress 6.4.2">
<link rel='stylesheet'
  href='https://shop.example/wp-content/plugins/contact-form-7/css/styles.css?ver=5.8.1' />
<script src="/wp-content/plugins/woocommerce/assets/js/frontend.min.js?ver=8.2.0"></script>
<script src="/wp-content/plugins/elementor/assets/js/x.js?ver=6.4.2"></script>
<script src="/wp-content/plugins/premium-thing/x.js"></script>"""


def test_plugin_versions_are_read_from_asset_urls():
    assert plugin_versions(PLUGIN_PAGE, "6.4.2") == {
        "contact-form-7": "5.8.1",
        "woocommerce": "8.2.0",
    }


def test_outdated_plugins_are_reported():
    plugins = {"contact-form-7": ("5.8.1", "5.9.8"), "woocommerce": ("8.2.0", "8.2.0")}
    finding = by_id(evaluate(detect(PLUGIN_PAGE), None, plugins))["cms.plugins-outdated"]
    assert finding.status is Status.FAIL
    assert [o.label for o in finding.observed] == ["contact-form-7"]
    assert finding.observed[0].value == "5.8.1 installed, 5.9.8 available"


def test_up_to_date_plugins_pass():
    plugins = {"woocommerce": ("8.2.0", "8.2.0")}
    finding = by_id(evaluate(detect(PLUGIN_PAGE), None, plugins))["cms.plugins-outdated"]
    assert finding.status is Status.PASS


def test_plugins_unknown_to_wordpress_org_are_skipped():
    results = by_id(evaluate(detect(PLUGIN_PAGE), None, {"premium": ("1.0", None)}))
    assert "cms.plugins-outdated" not in results
