"""Import an explicitly selected public GitHub repository into read-only workspace storage.

The web application never receives host write privileges. This CLI must run
on the trusted Docker host; it cannot import private/token-authenticated repos.
"""
import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

OWNER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
WORKSPACE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


def import_public_repository(
    identifier: str, workspace_root: Path, *, name: str | None = None,
    timeout: int = 120,
) -> Path:
    if identifier.count("/") != 1:
        raise ValueError("Use owner/repository format")
    owner, repository = identifier.split("/")
    if (not OWNER.fullmatch(owner) or not REPOSITORY.fullmatch(repository)
            or repository.endswith((".git", "."))):
        raise ValueError("Invalid public GitHub repository")
    destination_name = name or repository
    if (not WORKSPACE.fullmatch(destination_name) or destination_name.startswith(".")
            or destination_name.endswith(".")):
        raise ValueError("Invalid workspace folder name")
    if workspace_root.is_symlink():
        raise ValueError("Workspace root must not be a symlink")
    workspace_root.mkdir(parents=True, exist_ok=True)
    destination = workspace_root / destination_name
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Workspace already exists; no files were overwritten")
    staging = Path(tempfile.mkdtemp(prefix=".mmc-import-", dir=workspace_root))
    url = f"https://github.com/{owner}/{repository}.git"
    try:
        environ = dict(os.environ)
        environ.update({
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_LFS_SKIP_SMUDGE": "1",
        })
        try:
            result = subprocess.run(
                [
                    "git", "-c", "core.hooksPath=/dev/null",
                    "-c", "init.templateDir=",
                    "-c", "protocol.file.allow=never",
                    "-c", "protocol.ext.allow=never",
                    "clone", "--depth=1", "--single-branch", "--no-tags",
                    "--", url, str(staging),
                ],
                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                check=False, timeout=timeout, env=environ,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("GitHub import timed out") from exc
        if result.returncode != 0:
            raise RuntimeError("Unable to clone public GitHub repository")
        if destination.exists() or destination.is_symlink():
            raise FileExistsError("Workspace appeared during import; no files overwritten")
        staging.rename(destination)
        return destination
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import one public GitHub repo for read-only browsing")
    parser.add_argument("repository", help="owner/repository")
    parser.add_argument("--name", help="workspace folder name; defaults to repository name")
    parser.add_argument("--root", type=Path, default=Path("workspaces"), help="approved host workspace folder")
    arguments = parser.parse_args()
    try:
        path = import_public_repository(arguments.repository, arguments.root, name=arguments.name)
    except (ValueError, FileExistsError, OSError, RuntimeError) as exc:
        parser.exit(1, f"Import failed: {exc}\n")
    print(f"Imported public repository into {path}.")
    print("The web container sees it through the existing read-only mount.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
