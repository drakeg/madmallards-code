"""Constrained, read-only browsing of administrator-mounted local workspaces."""
import difflib
import hashlib
import os
import re
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])
WORKSPACE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
TEXT_EXTENSIONS = frozenset({
    ".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml",
    ".js", ".jsx", ".ts", ".tsx", ".css", ".html", ".sh",
    ".sql", ".go", ".rs", ".java", ".xml", ".ini", ".cfg",
})
TEXT_NAMES = frozenset({"Dockerfile", "Makefile", "LICENSE", "Containerfile"})
BLOCKED_PARTS = frozenset({
    ".git", ".env", ".ssh", ".aws", ".kube", "node_modules",
    "__pycache__", ".venv", "venv", ".next", "dist", "build",
})
MAX_FILE_BYTES = 128 * 1024
MAX_ENTRIES = 250


def workspace_root() -> Path:
    return Path(os.environ.get("WORKSPACES_ROOT", "/workspaces")).resolve()


def allowed_name(name: str) -> bool:
    return bool(
        name and not name.startswith(".") and name not in BLOCKED_PARTS
        and not name.endswith("~") and not name.endswith(".pem")
    )


def safe_path(root: Path, workspace: str, relative: str = "") -> Path:
    if not WORKSPACE_NAME.fullmatch(workspace) or not allowed_name(workspace):
        raise HTTPException(400, "Invalid workspace name")
    if "\\" in relative or "\x00" in relative:
        raise HTTPException(400, "Invalid path")
    pieces = relative.split("/") if relative else []
    if any(piece in {"", ".", ".."} or not allowed_name(piece) for piece in pieces):
        raise HTTPException(400, "Invalid path")
    base = root / workspace
    if not base.is_dir() or base.is_symlink():
        raise HTTPException(404, "Workspace not found")
    candidate = base
    for segment in pieces:
        candidate = candidate / segment
        if candidate.is_symlink():
            raise HTTPException(403, "Symlinks are not browsable")
    if not candidate.exists():
        raise HTTPException(404, "Path not found")
    try:
        candidate.resolve(strict=True).relative_to(base.resolve(strict=True))
    except (ValueError, OSError):
        raise HTTPException(403, "Path is outside the workspace") from None
    return candidate


@router.get("")
def list_workspaces(root: Annotated[Path, Depends(workspace_root)]) -> dict:
    if not root.is_dir():
        return {"workspaces": []}
    return {
        "workspaces": [
            {"name": item.name}
            for item in sorted(root.iterdir(), key=lambda x: x.name.casefold())
            if item.is_dir() and not item.is_symlink()
            and WORKSPACE_NAME.fullmatch(item.name) and allowed_name(item.name)
        ][:MAX_ENTRIES]
    }


@router.get("/{workspace}/tree")
def list_tree(
    workspace: str,
    root: Annotated[Path, Depends(workspace_root)],
    path: str = Query(default="", max_length=2048),
) -> dict:
    directory = safe_path(root, workspace, path)
    if not directory.is_dir():
        raise HTTPException(400, "Not a directory")
    entries = []
    for item in sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.casefold())):
        if len(entries) >= MAX_ENTRIES:
            break
        if item.is_symlink() or not allowed_name(item.name):
            continue
        if item.is_dir():
            kind = "directory"
        elif item.is_file():
            kind = "file"
        else:
            continue
        entries.append({"name": item.name, "kind": kind})
    return {"workspace": workspace, "path": path, "entries": entries}


@router.get("/{workspace}/file")
def view_file(
    workspace: str,
    root: Annotated[Path, Depends(workspace_root)],
    path: str = Query(min_length=1, max_length=2048),
) -> dict:
    candidate = safe_path(root, workspace, path)
    if not candidate.is_file():
        raise HTTPException(400, "Not a file")
    if candidate.suffix.lower() not in TEXT_EXTENSIONS and candidate.name not in TEXT_NAMES:
        raise HTTPException(415, "File type not supported")
    if candidate.stat().st_size > MAX_FILE_BYTES:
        raise HTTPException(413, "File too large to preview")
    try:
        content = candidate.read_text(encoding="utf-8")
    except (UnicodeError, OSError):
        raise HTTPException(415, "Cannot preview file") from None
    return {
        "workspace": workspace,
        "path": path,
        "content": content,
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "read_only": True,
    }


class ProposalRequest(BaseModel):
    path: str = Field(min_length=1, max_length=2048)
    baseline_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    proposed_content: str = Field(max_length=128 * 1024)


@router.post("/{workspace}/proposals")
def preview_proposal(
    workspace: str,
    payload: ProposalRequest,
    root: Annotated[Path, Depends(workspace_root)],
) -> dict:
    """Produce a unified diff without modifying the workspace."""
    original = view_file(workspace, root, payload.path)
    if original["sha256"] != payload.baseline_sha256:
        raise HTTPException(status_code=409, detail="File changed; reload before proposing edits")
    old_lines = original["content"].splitlines(keepends=True)
    new_lines = payload.proposed_content.splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{payload.path}",
        tofile=f"b/{payload.path}",
        n=3,
    ))
    return {
        "workspace": workspace,
        "path": payload.path,
        "changed": bool(diff),
        "diff": diff,
        "read_only": True,
        "applied": False,
    }
