"""Verify selected mascot identity and company attribution across the app."""
from pathlib import Path
from xml.etree import ElementTree

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = ROOT / "app" / "static" / "brand"


def test_product_and_parent_company_are_distinct():
    with TestClient(app) as client:
        html = client.get("/").text
        logo = client.get("/static/brand/mad-mallards-code-logo.svg")
        favicon = client.get("/static/brand/favicon.svg")
    assert "Mad Mallards Code | By Mad Mallard Solutions" in html
    assert 'class="brand-art"' in html
    assert 'class="welcome-brand"' in html
    assert 'rel="icon" type="image/svg+xml"' in html
    assert logo.status_code == 200
    assert favicon.status_code == 200
    assert "MAD MALLARD SOLUTIONS" in logo.text
    assert "Mad Mallards Code" in logo.text
    assert "Adventures" not in html + logo.text
    assert ElementTree.fromstring(logo.text).tag.endswith("svg")
    assert ElementTree.fromstring(favicon.text).tag.endswith("svg")


def test_login_logo_available_without_login_and_other_assets_protected(tmp_path, monkeypatch):
    # This fixture must use the actual authentication middleware rather than
    # the bypass used in legacy UI tests.
    from app import main

    monkeypatch.setattr(main, "authenticated", lambda request: False)
    with TestClient(app, follow_redirects=False) as client:
        assert client.get("/auth/login").status_code == 200
        assert client.get("/static/brand/mad-mallards-code-logo.svg").status_code == 200
        assert client.get("/static/brand/favicon.svg").status_code == 200
        assert client.get("/static/chat.css").status_code == 303
        assert client.get("/api/v1/workspaces").status_code == 401


def test_brand_source_has_no_external_font_or_image_dependencies():
    for path in BRAND_DIR.glob("*.svg"):
        body = path.read_text()
        assert "http://www.w3.org/2000/svg" in body
        assert "url(https:" not in body
        assert "<image" not in body
        assert "<script" not in body
