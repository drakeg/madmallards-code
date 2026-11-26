"""Public workspace importer safety and non-overwrite tests."""
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts import import_public_repo as importer


def test_public_clone_is_bounded_and_non_destructive(tmp_path, monkeypatch):
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        staging = Path(argv[-1])
        (staging / "README.md").write_text("hello")
        (staging / ".git").mkdir()
        return Mock(returncode=0)

    monkeypatch.setattr(importer.subprocess, "run", fake_run)
    target = importer.import_public_repository("drakeg/madmallards-code", tmp_path)
    assert target.name == "madmallards-code"
    assert (target / "README.md").read_text() == "hello"
    assert calls[0][0][-2] == "https://github.com/drakeg/madmallards-code.git"
    assert "--depth=1" in calls[0][0]
    assert calls[0][1]["timeout"] == 120
    assert calls[0][1]["env"]["GIT_TERMINAL_PROMPT"] == "0"
    assert calls[0][1]["env"]["GIT_CONFIG_GLOBAL"] == "/dev/null"
    assert calls[0][1]["stdin"] == subprocess.DEVNULL
    with pytest.raises(FileExistsError):
        importer.import_public_repository("drakeg/madmallards-code", tmp_path)
    assert len(calls) == 1
    assert (target / "README.md").read_text() == "hello"


@pytest.mark.parametrize("identifier", [
    "drakeg", "../drakeg", "drakeg/../repo", "drakeg/.hidden",
    "drakeg/repo.git", "https://github.com/drakeg/repo",
    "drakeg/repo/extra", "foo_bar/repo",
])
def test_rejects_invalid_names_without_clone(tmp_path, monkeypatch, identifier):
    def unwanted(*args, **kwargs):
        raise AssertionError("Git must not run for invalid input")

    monkeypatch.setattr(importer.subprocess, "run", unwanted)
    with pytest.raises(ValueError):
        importer.import_public_repository(identifier, tmp_path)


def test_root_symlink_rejected(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(target)
    with pytest.raises(ValueError):
        importer.import_public_repository("drakeg/repo", alias)


def test_failed_clone_cleans_up_staging(tmp_path, monkeypatch):
    monkeypatch.setattr(
        importer.subprocess, "run", lambda *args, **kwargs: Mock(returncode=128)
    )
    with pytest.raises(RuntimeError, match="Unable to clone"):
        importer.import_public_repository("drakeg/repo", tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_timeout_cleans_up_staging(tmp_path, monkeypatch):
    def timeout(args, **kwargs):
        raise subprocess.TimeoutExpired(args, 120)

    monkeypatch.setattr(importer.subprocess, "run", timeout)
    with pytest.raises(RuntimeError, match="timed out"):
        importer.import_public_repository("drakeg/repo", tmp_path)
    assert list(tmp_path.iterdir()) == []
