import pytest

from vigilo.lab import LabConfigError, parse_lab_targets


def test_lab_targets_are_parsed():
    targets = parse_lab_targets("juice.lab=http://127.0.0.1:8080/, dvwa.test=http://10.0.0.5")
    assert set(targets) == {"juice.lab", "dvwa.test"}
    assert targets["juice.lab"].base_url == "http://127.0.0.1:8080"
    assert targets["juice.lab"].scan_url == "http://juice.lab/"
    assert targets["juice.lab"].network == "vigilo-lab"


def test_empty_configuration_means_no_lab():
    assert parse_lab_targets("") == {}


@pytest.mark.parametrize(
    "raw",
    [
        "example.com=http://127.0.0.1:8080",  # a real domain can never be a lab
        "shop.lab.example.com=http://127.0.0.1",  # suffix must be the last label
        ".lab=http://127.0.0.1",
        "juice.lab=http://93.184.215.14",  # a public address
        "juice.lab=http://evil.example",  # a name could resolve anywhere
        "juice.lab=ftp://127.0.0.1",
        "juice.lab",
        "juice.lab=",
    ],
)
def test_anything_that_is_not_a_lab_is_refused(raw):
    with pytest.raises(LabConfigError):
        parse_lab_targets(raw)
