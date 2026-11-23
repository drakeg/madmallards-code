"""Workspace boundary and read-only browsing tests."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.workspaces import workspace_root


@pytest.fixture
def client(tmp_path):
    workspace = tmp_path / "example"
    workspace.mkdir()
    (workspace / "README.md").write_text("# Safe repo\n", encoding="utf-8")
    (workspace / "app").mkdir()
    (workspace / "app" / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (workspace / ".env").write_text("SECRET=value")
    (workspace / "large.md").write_text("a" * (128 * 1024 + 1))
    (workspace / "binary.bin").write_bytes(b"\x00\x01")
    (workspace / "secret-link").symlink_to(tmp_path / "secret.txt")
    (tmp_path / "secret.txt").write_text("private")
    app.dependency_overrides[workspace_root] = lambda: tmp_path
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_list_and_browse(client):
    assert client.get("/api/v1/workspaces").json()["workspaces"] == [{"name": "example"}]
    tree = client.get("/api/v1/workspaces/example/tree").json()["entries"]
    assert any(item["name"] == "app" and item["kind"] == "directory" for item in tree)
    assert not any(item["name"] in {".env", "secret-link"} for item in tree)
    assert client.get("/api/v1/workspaces/example/tree", params={"path": "app"}).json()["entries"] == [
        {"name": "main.py", "kind": "file"}
    ]
    file = client.get("/api/v1/workspaces/example/file", params={"path": "README.md"})
    assert file.status_code == 200
    assert file.json()["content"] == "# Safe repo\n"
    assert file.json()["read_only"] is True


@pytest.mark.parametrize("path", [
    "../secret.txt", "app/../../secret.txt", "/etc/passwd", ".env", "secret-link",
    "app//main.py", "app/./main.py", "app/../README.md",
])
def test_denied_paths(client, path):
    assert client.get("/api/v1/workspaces/example/file", params={"path": path}).status_code in {400, 403, 404}


def test_unsupported_and_large_files(client):
    assert client.get("/api/v1/workspaces/example/file", params={"path": "binary.bin"}).status_code == 415
    assert client.get("/api/v1/workspaces/example/file", params={"path": "large.md"}).status_code == 413
    assert client.get("/api/v1/workspaces/no-such-repo/tree").status_code == 404
    assert client.post("/api/v1/workspaces/example/file", params={"path": "README.md"}).status_code == 405
