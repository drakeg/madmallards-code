"""Run Python unittest suites in a disposable, network-isolated Docker sandbox.

Host-only CLI: no web endpoint, Docker socket mount, privileged mode, or shell.
The repository is mounted read-only and cannot be modified by the test process.
"""
import argparse
import re
import subprocess
from pathlib import Path

VALID_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
IMAGE = "python:3.15-slim"
TIMEOUT = 90
MAX_OUTPUT = 16_000


def validate_workspace(root: Path, name: str) -> Path:
    if not VALID_NAME.fullmatch(name) or name.endswith("."):
        raise ValueError("Invalid workspace name")
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Workspace root must be an existing directory, not a symlink")
    workspace = root / name
    if workspace.is_symlink() or not workspace.is_dir():
        raise ValueError("Workspace not found or is a symlink")
    try:
        workspace.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ValueError("Workspace path is outside approved root") from exc
    tests = workspace / "tests"
    if tests.is_symlink() or not tests.is_dir():
        raise ValueError("Workspace must contain a real tests/ directory")
    return workspace.resolve(strict=True)


def run_tests(root: Path, name: str) -> tuple[int, str]:
    workspace = validate_workspace(root, name)
    command = [
        "docker", "run", "--rm", "--pull=never",
        "--network=none", "--read-only", "--cap-drop=ALL",
        "--security-opt", "no-new-privileges:true",
        "--user", "65534:65534",
        "--pids-limit", "64", "--memory", "512m", "--memory-swap", "512m",
        "--cpus", "1.0", "--ulimit", "nofile=128:128",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        "--env", "HOME=/tmp",
        "--mount", f"type=bind,src={workspace},dst=/workspace,readonly",
        "--workdir", "/workspace",
        IMAGE, "python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py",
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True, text=True, timeout=TIMEOUT, check=False,
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return 1, "Docker CLI is unavailable"
    except subprocess.TimeoutExpired:
        return 1, "Sandbox execution timed out"
    output = (result.stdout + "\n" + result.stderr)[-MAX_OUTPUT:]
    if "Ran 0 tests" in output and result.returncode == 0:
        return 1, "No unittest tests discovered; no success claimed"
    return result.returncode, output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a fixed unittest suite inside a read-only sandbox")
    parser.add_argument("workspace", help="folder under approved workspaces root")
    parser.add_argument("--root", type=Path, default=Path("workspaces"))
    arguments = parser.parse_args()
    try:
        status, output = run_tests(arguments.root, arguments.workspace)
    except ValueError as exc:
        parser.exit(1, f"Sandbox validation failed: {exc}\n")
    print(output)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
