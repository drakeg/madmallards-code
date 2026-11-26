"""Verify core controls survive the Creative Studio workbench redesign."""
from fastapi.testclient import TestClient

from app.main import app


def test_workbench_preserves_functional_controls():
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    html = response.text
    for name in (
        "sidebar-toggle", "workspace-sidebar", "new-chat", "conversation-list",
        "workspace-select", "workspace-tree", "github-form", "github-load",
        "github-results", "model-select", "conversation-title", "messages",
        "empty-state", "prompt", "composer", "send-button", "cancel-button",
        "file-preview", "preview-proposal", "ai-preview-proposal",
        "download-proposal-patch", "logout-button",
    ):
        assert f'id="{name}"' in html
    assert 'aria-controls="workspace-sidebar"' in html
    assert 'aria-expanded="false"' in html
    assert 'data-prompt=' in html
    assert 'src="/static/workbench.js"' in html
    assert 'href="/static/chat.css"' in html


def test_mobile_accessibility_and_assets():
    with TestClient(app) as client:
        script = client.get("/static/workbench.js")
        style = client.get("/static/chat.css")
    assert script.status_code == 200
    assert style.status_code == 200
    assert "event.metaKey || event.ctrlKey" in script.text
    assert 'event.key === "Escape"' in script.text
    assert "button.dataset.prompt" in script.text
    assert "setSidebarOpen(false)" in script.text
    assert "prefers-reduced-motion:reduce" in style.text
    assert ":focus-visible" in style.text
    assert "@media (max-width:767.98px)" in style.text
    assert ".starter-grid" in style.text
    assert ".sidebar.is-open" in style.text


def test_no_automatic_prompt_submission_on_suggestion():
    with TestClient(app) as client:
        script = client.get("/static/workbench.js").text
    assert "prompt.value = button.dataset.prompt" in script
    assert "form.requestSubmit" not in script
    assert "fetch(" not in script
