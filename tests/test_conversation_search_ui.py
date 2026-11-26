"""Conversation search and local CSS dependencies remain usable in the workbench."""
from fastapi.testclient import TestClient

from app.main import app


def test_conversation_search_controls_and_filter_code():
    with TestClient(app) as browser:
        html = browser.get("/").text
        script = browser.get("/static/chat.js").text
    assert 'id="conversation-filter"' in html
    assert 'id="conversation-filter-status"' in html
    assert 'aria-controls="conversation-list"' in html
    assert 'addEventListener("input", filterConversations)' in script
    assert 'item.textContent.toLocaleLowerCase().includes(search)' in script
    assert "filterConversations();" in script
    assert 'item.hidden = Boolean(search' in script


def test_workbench_local_style_and_desktop_scroll_contract():
    with TestClient(app) as browser:
        html = browser.get("/").text
        style = browser.get("/static/chat.css").text
        bootstrap = browser.get("/static/vendor/bootstrap/bootstrap.min.css")
    assert 'href="/static/vendor/bootstrap/bootstrap.min.css"' in html
    assert "cdn.jsdelivr.net" not in html
    assert bootstrap.status_code == 200
    assert "Bootstrap" in bootstrap.text[:1000] and "v5.3.3" in bootstrap.text[:1000]
    assert '.shell {height:calc(100dvh - 74px);min-height:0}' in style
    assert '.chat-scroll {flex:1;min-height:0;max-height:none;overflow-y:auto' in style
    assert '  .shell,.shell>.row {height:auto;' in style
