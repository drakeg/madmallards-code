"""README badge claims must track verified manifests and dynamic GitHub states."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_badges_reflect_current_manifests_and_workflow():
    readme = (ROOT / "README.md").read_text()
    top = readme.splitlines()
    assert top[0] == "# Mad Mallards Code"
    badge_rows = top[2:5]
    assert len(badge_rows) == 3
    assert all("[![" in row for row in badge_rows)
    badges = "\n".join(badge_rows)
    for required in [
        "actions/workflows/ci.yml/badge.svg",
        "img.shields.io/github/license/drakeg/madmallards-code",
        "img.shields.io/github/issues/drakeg/madmallards-code",
        "img.shields.io/github/issues-pr/drakeg/madmallards-code",
        "img.shields.io/github/v/release/drakeg/madmallards-code",
    ]:
        assert required in badges
    assert "FROM python:3.15-slim" in (ROOT / "Dockerfile").read_text()
    assert "Python-3.15" in badges
    assert "image: mariadb:11.8" in (ROOT / "compose.yaml").read_text()
    assert "MariaDB-11.8" in badges
    assert "fastapi" in (ROOT / "requirements.txt").read_text().lower()
    assert "FastAPI-framework" in badges
    assert "name: CI" in (ROOT / ".github/workflows/ci.yml").read_text()
    assert "Docker-Compose" in badges
    assert len(re.findall("img.shields.io/github/license/", badges)) == 1


def test_no_stale_unauthenticated_or_no_model_claims():
    readme = (ROOT / "README.md").read_text()
    for obsolete in [
        "No AI model calls",
        "currently an unauthenticated",
        "single-user localhost MVP",
        "application is bound to localhost",
        "single shared password",
    ]:
        assert obsolete not in readme
    assert "MariaDB-backed login" in readme
    assert "HTTP" in readme


def test_required_project_standards_documented():
    for filename in ("AGENTS.md", "CONTRIBUTING.md", "RELEASES.md", "LICENSE"):
        assert (ROOT / filename).is_file()
    assert (ROOT / "docs/SPRINTS.md").is_file()
    assert (ROOT / "docs/BACKLOG.md").is_file()
