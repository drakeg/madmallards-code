"""Read-only public GitHub repository status. No tokens or repository writes."""
import re
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/v1/github", tags=["github"])

NAME = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_-]{0,38})$")
REPO = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")


class GitHubPublic:
    async def overview(self, owner: str, repo: str) -> dict:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "MadMallardsCode-ReadOnly/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        async with httpx.AsyncClient(
            base_url="https://api.github.com",
            headers=headers, timeout=10, follow_redirects=False,
        ) as client:
            async def fetch(path: str, params: dict | None = None):
                try:
                    response = await client.get(path, params=params)
                except httpx.RequestError as exc:
                    raise HTTPException(503, "GitHub cannot be reached") from exc
                if response.status_code == 404:
                    raise HTTPException(404, "Public repository not found")
                if response.status_code in {403, 429}:
                    raise HTTPException(503, "GitHub API rate limit or access restriction")
                if response.status_code != 200:
                    raise HTTPException(502, "GitHub returned an unexpected response")
                try:
                    return response.json()
                except ValueError as exc:
                    raise HTTPException(502, "Invalid response from GitHub") from exc

            prefix = f"/repos/{owner}/{repo}"
            metadata = await fetch(prefix)
            if metadata.get("private") or metadata.get("full_name", "").lower() != f"{owner}/{repo}".lower():
                raise HTTPException(404, "Public repository not found")
            branches = await fetch(prefix + "/branches", {"per_page": 12})
            pulls = await fetch(prefix + "/pulls", {"state": "open", "per_page": 12})
            workflows = await fetch(prefix + "/actions/runs", {"per_page": 10})
        if not isinstance(branches, list) or not isinstance(pulls, list) or not isinstance(workflows, dict):
            raise HTTPException(502, "Unexpected GitHub response")
        return {
            "name": metadata["full_name"],
            "description": metadata.get("description") or "",
            "default_branch": metadata.get("default_branch") or "main",
            "url": metadata.get("html_url") or "",
            "branches": [
                {"name": item.get("name", ""), "protected": bool(item.get("protected", False))}
                for item in branches
            ],
            "pull_requests": [
                {
                    "number": item.get("number"),
                    "title": item.get("title") or "",
                    "url": item.get("html_url") or "",
                    "draft": bool(item.get("draft", False)),
                }
                for item in pulls
            ],
            "runs": [
                {
                    "name": item.get("name") or "Workflow",
                    "branch": item.get("head_branch") or "",
                    "status": item.get("status") or "unknown",
                    "conclusion": item.get("conclusion"),
                    "url": item.get("html_url") or "",
                }
                for item in workflows.get("workflow_runs", [])
            ][:10],
            "read_only": True,
            "source": "GitHub public API",
        }


def github_provider() -> GitHubPublic:
    return GitHubPublic()


@router.get("/{owner}/{repository}")
async def repository_overview(
    owner: str,
    repository: str,
    source: Annotated[GitHubPublic, Depends(github_provider)],
) -> dict:
    if not NAME.fullmatch(owner) or not REPO.fullmatch(repository):
        raise HTTPException(422, "Invalid GitHub repository identifier")
    if repository.startswith(".") or repository.endswith(".") or repository.endswith(".git"):
        raise HTTPException(422, "Invalid GitHub repository name")
    return await source.overview(owner, repository)
