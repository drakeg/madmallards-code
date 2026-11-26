"""Read-only public GitHub status with isolated mocked HTTP requests."""
import httpx
import pytest
from fastapi.testclient import TestClient

from app.github_status import GitHubPublic, github_provider
from app.main import app


class FakeGitHub(GitHubPublic):
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def overview(self, owner, repo):
        # Exercise production GitHubPublic HTTP parsing with a mocked transport.
        original = httpx.AsyncClient

        def factory(*args, **kwargs):
            return original(
                *args,
                transport=httpx.MockTransport(self.respond),
                **kwargs,
            )

        from unittest.mock import patch
        with patch("app.github_status.httpx.AsyncClient", factory):
            return await super().overview(owner, repo)

    def respond(self, request):
        self.calls.append((request.method, request.url.path))
        assert request.method == "GET"
        return httpx.Response(
            self.responses.get(request.url.path, (404, {"message": "Not found"}))[0],
            json=self.responses.get(request.url.path, (404, {"message": "Not found"}))[1],
        )


@pytest.fixture
def client():
    repo = "/repos/drakeg/madmallards-code"
    stub = FakeGitHub({
        repo: (200, {
            "full_name": "drakeg/madmallards-code", "private": False,
            "description": "Self-hosted coding assistant",
            "default_branch": "main",
            "html_url": "https://github.com/drakeg/madmallards-code",
        }),
        repo + "/branches": (200, [{"name": "main", "protected": True}]),
        repo + "/pulls": (200, [{
            "number": 32, "title": "Auth update", "draft": False,
            "html_url": "https://github.com/drakeg/madmallards-code/pull/32",
        }]),
        repo + "/actions/runs": (200, {"workflow_runs": [{
            "name": "CI", "head_branch": "main", "status": "completed",
            "conclusion": "success",
            "html_url": "https://github.com/drakeg/madmallards-code/actions/runs/123",
        }]}),
    })
    app.dependency_overrides[github_provider] = lambda: stub
    try:
        with TestClient(app) as instance:
            yield instance, stub
    finally:
        app.dependency_overrides.clear()


def test_public_overview_and_get_only(client):
    browser, stub = client
    response = browser.get("/api/v1/github/drakeg/madmallards-code")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == "drakeg/madmallards-code"
    assert body["branches"] == [{"name": "main", "protected": True}]
    assert body["pull_requests"][0]["number"] == 32
    assert body["runs"][0]["conclusion"] == "success"
    assert body["read_only"] is True
    assert len(stub.calls) == 4
    assert all(method == "GET" for method, _ in stub.calls)
    assert browser.post("/api/v1/github/drakeg/madmallards-code").status_code == 405


@pytest.mark.parametrize("path", [
    "bad.owner/repo", "owner/.env", "owner/repo.git", "a" * 40 + "/repo",
    "owner/" + "a" * 101,
])
def test_invalid_identifiers_do_not_call_github(client, path):
    browser, stub = client
    assert browser.get("/api/v1/github/" + path).status_code == 422
    assert not stub.calls


def test_upstream_not_found_and_rate_limited(client):
    browser, stub = client
    repo = "/repos/drakeg/madmallards-code"
    stub.responses[repo] = (404, {"message": "Not found"})
    assert browser.get("/api/v1/github/drakeg/madmallards-code").status_code == 404
    stub.responses[repo] = (403, {"message": "API rate limit exceeded"})
    assert browser.get("/api/v1/github/drakeg/madmallards-code").status_code == 503


def test_private_repository_cannot_be_reported(client):
    browser, stub = client
    repo = "/repos/drakeg/madmallards-code"
    stub.responses[repo][1]["private"] = True
    assert browser.get("/api/v1/github/drakeg/madmallards-code").status_code == 404
    assert len(stub.calls) == 1


def test_github_ui_is_present(client):
    browser, _ = client
    html = browser.get("/").text
    assert 'id="github-form"' in html
    assert 'id="github-results"' in html
    assert browser.get("/static/github.js").status_code == 200
