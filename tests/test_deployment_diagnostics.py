"""Safe diagnostics must never modify Docker or disclose command stderr."""
import importlib.util
import subprocess
from pathlib import Path
from unittest.mock import Mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_deployment.py"
spec = importlib.util.spec_from_file_location("deployment_diag", SCRIPT)
diagnostics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostics)


def test_engine_timeout_prevents_container_query(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        raise subprocess.TimeoutExpired(args, 5)

    monkeypatch.setattr(diagnostics.subprocess, "run", fake_run)
    monkeypatch.setattr(diagnostics, "http_check", lambda port: {"status": "error"})
    result = diagnostics.diagnose()
    assert result["docker_engine"]["status"] == "timeout"
    assert result["containers"]["status"] == "skipped"
    assert calls == [["docker", "info", "--format", "{{.ServerVersion}}"]]


def test_healthy_engine_queries_only_read_operations(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return Mock(returncode=0, stdout="healthy\n", stderr="DO_NOT_LEAK")

    monkeypatch.setattr(diagnostics.subprocess, "run", fake_run)
    monkeypatch.setattr(diagnostics, "http_check", lambda port: {"status": "ok"})
    result = diagnostics.diagnose()
    assert result["containers"]["status"] == "ok"
    assert len(calls) == 2
    assert calls[1][-4:] == ["ps", "--all", "--format", "json"]
    assert "DO_NOT_LEAK" not in str(result)
    assert all("down" not in call and "restart" not in call for call in calls)


def test_cli_missing(monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError("docker")

    monkeypatch.setattr(diagnostics.subprocess, "run", missing)
    assert diagnostics.command_check(["docker", "info"])["status"] == "missing"


def test_health_fails_closed(monkeypatch):
    def missing(*args, **kwargs):
        raise ConnectionRefusedError("connection refused")

    monkeypatch.setattr(diagnostics.urllib.request, "urlopen", missing)
    assert diagnostics.http_check()["status"] == "error"
