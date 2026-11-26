import asyncio
import shlex
import sys

import pytest

from vigilo.active import runner
from vigilo.active.runner import (
    NUCLEI_EXCLUDED_TAGS,
    ZAP_REPORT_MARKER,
    Limits,
    ScanPlan,
    ToolFailed,
    ToolRun,
    docker_runner,
    nuclei_run,
    tool_runs,
    zap_report,
    zap_run,
)

PUBLIC = ScanPlan(
    domain="shop.example", target_url="https://shop.example/", pinned_address="203.0.113.7"
)
LAB = ScanPlan(domain="juice.lab", target_url="http://juice.lab/", network="vigilo-lab")


def value_after(argv, flag):
    return [argv[i + 1] for i, a in enumerate(argv) if a == flag]


@pytest.mark.parametrize("build", [nuclei_run, zap_run])
def test_containers_are_locked_down(build):
    argv = build(PUBLIC).argv
    assert argv[1:3] == ["run", "--rm"]
    assert "--read-only" in argv
    assert value_after(argv, "--cap-drop") == ["ALL"]
    assert value_after(argv, "--security-opt") == ["no-new-privileges"]
    for flag in ("--memory", "--memory-swap", "--cpus", "--pids-limit", "--name"):
        assert value_after(argv, flag), flag
    assert "--privileged" not in argv
    assert not any(a.startswith(("-v", "--volume")) for a in argv), "no host directory mounted"


def test_outside_the_lab_only_the_verified_host_resolves():
    argv = nuclei_run(PUBLIC).argv
    assert value_after(argv, "--dns") == ["0.0.0.0"]
    assert value_after(argv, "--add-host") == ["shop.example:203.0.113.7"]


def test_in_the_lab_the_lab_network_is_used():
    argv = nuclei_run(LAB).argv
    assert value_after(argv, "--network") == ["vigilo-lab"]
    assert "--dns" not in argv
    assert "--add-host" not in argv


def test_nuclei_runs_safe_checks_only():
    argv = nuclei_run(PUBLIC).argv
    excluded = value_after(argv, "-exclude-tags")[0].split(",")
    for tag in ("dos", "intrusive", "fuzz", "bruteforce", "rce", "sqli", "oast"):
        assert tag in excluded
    assert set(excluded) == set(NUCLEI_EXCLUDED_TAGS)
    assert "-no-interactsh" in argv
    assert value_after(argv, "-target") == ["https://shop.example/"]
    templates_mount = next(a for a in argv if "target=/templates" in a)
    assert templates_mount.endswith(",readonly")


def test_zap_runs_the_baseline_and_quotes_the_target():
    plan = ScanPlan(
        domain="x.example", target_url="https://x.example/;rm -rf /", pinned_address="203.0.113.7"
    )
    script = zap_run(plan).argv[-1]
    assert script.startswith("zap-baseline.py ")
    assert shlex.quote("https://x.example/;rm -rf /") in script
    assert "zap-full-scan" not in script


def test_both_tools_by_default():
    assert [r.tool for r in tool_runs(PUBLIC)] == ["nuclei", "zap"]


def test_zap_report_is_read_after_the_marker():
    assert zap_report(f'log line\n{ZAP_REPORT_MARKER}\n{{"site": []}}\n') == '{"site": []}'
    assert zap_report("ZAP crashed before writing a report") == ""


# --- execution, with a local process standing in for docker ---------------------------


def python_run(code: str, seconds: float = 10) -> ToolRun:
    return ToolRun("nuclei", [sys.executable, "-c", code], Limits("1g", "1", seconds=seconds))


def test_runner_returns_standard_output():
    assert asyncio.run(docker_runner(python_run("print('result')"))).strip() == "result"


def test_runner_stops_a_tool_at_its_time_limit():
    with pytest.raises(ToolFailed, match="time limit"):
        asyncio.run(docker_runner(python_run("import time; time.sleep(30)", seconds=0.5)))


def test_a_failed_tool_without_output_is_an_error():
    with pytest.raises(ToolFailed, match="exit code 3"):
        asyncio.run(docker_runner(python_run("import sys; sys.exit(3)")))


def test_output_is_capped(monkeypatch):
    monkeypatch.setattr(runner, "MAX_OUTPUT_BYTES", 1000)
    output = asyncio.run(docker_runner(python_run("print('x' * 100000)")))
    assert len(output) == 1000
