"""Enforce sandbox allowlist and fail-closed behavior without running user code."""
import subprocess
from unittest.mock import Mock

import pytest

from scripts import run_isolated_tests as runner


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "workspaces"
    project = root / "example"
    tests = project / "tests"
    tests.mkdir(parents=True)
    (tests / "test_example.py").write_text("import unittest\n")
    return root, project


def test_runner_has_no_network_host_writes_or_shell(workspace, monkeypatch):
    root, project = workspace
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return Mock(returncode=0, stdout="", stderr="Ran 1 test in 0.001s\nOK\n")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    status, output = runner.run_tests(root, "example")
    assert status == 0
    assert "Ran 1 test" in output
    argv, options = calls[0]
    assert argv[:3] == ["docker", "run", "--rm"]
    for expected in [
        "--network=none", "--read-only", "--cap-drop=ALL",
        "no-new-privileges:true", "--pids-limit", "--memory", "--cpus",
        "--pull=never",
    ]:
        assert expected in argv
    assert f"type=bind,src={project.resolve()},dst=/workspace,readonly" in argv
    assert not any("docker.sock" in item for item in argv)
    assert argv[-8:] == [
        "python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"
    ]
    assert options["timeout"] == 90
    assert options["stdin"] == subprocess.DEVNULL
    assert options["check"] is False
    assert not options.get("shell")


@pytest.mark.parametrize("name", [".secret", "../example", "bad/name", "bad\\path", "a" * 81])
def test_bad_names_fail_before_docker(workspace, monkeypatch, name):
    root, _ = workspace
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **kw: pytest.fail("docker must not run"))
    with pytest.raises(ValueError):
        runner.run_tests(root, name)


def test_symlink_and_missing_tests_rejected(workspace, tmp_path):
    root, project = workspace
    alias = root / "alias"
    alias.symlink_to(project)
    with pytest.raises(ValueError):
        runner.validate_workspace(root, "alias")
    (project / "tests").rename(project / "other")
    with pytest.raises(ValueError):
        runner.validate_workspace(root, "example")


def test_timeout_returns_failure(workspace, monkeypatch):
    root, _ = workspace

    def timeout(args, **kwargs):
        raise subprocess.TimeoutExpired(args, 90)

    monkeypatch.setattr(runner.subprocess, "run", timeout)
    assert runner.run_tests(root, "example")[0] == 1


def test_zero_tests_is_not_success(workspace, monkeypatch):
    root, _ = workspace
    monkeypatch.setattr(
        runner.subprocess, "run",
        lambda *args, **kwargs: Mock(returncode=0, stdout="", stderr="Ran 0 tests\nOK"),
    )
    assert runner.run_tests(root, "example")[0] == 1


def test_failure_output_is_bounded(workspace, monkeypatch):
    root, _ = workspace
    monkeypatch.setattr(
        runner.subprocess, "run",
        lambda *args, **kwargs: Mock(returncode=1, stdout="X" * 30000, stderr="failure"),
    )
    status, output = runner.run_tests(root, "example")
    assert status == 1
    assert len(output) <= 16000
    assert "failure" in output
