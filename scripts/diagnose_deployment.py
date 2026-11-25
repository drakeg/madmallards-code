"""Read-only, timeout-bounded diagnosis for Mad Mallards Code."""
import argparse
import json
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def command_check(args: list[str], timeout: int = 5) -> dict:
    try:
        result = subprocess.run(args, text=True, capture_output=True, check=False, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "message": "Command exceeded safety timeout"}
    except FileNotFoundError:
        return {"status": "missing", "message": "Docker CLI not installed"}
    if result.returncode:
        return {"status": "error", "message": f"Command exit status {result.returncode}"}
    return {"status": "ok", "output": result.stdout.strip()[:2000]}


def http_check(port: int = 8096, timeout: int = 4) -> dict:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=timeout) as response:
            if response.status != 200 or json.load(response).get("status") != "ok":
                return {"status": "error", "message": "Unhealthy response"}
    except (OSError, ValueError):
        return {"status": "error", "message": "Health endpoint unavailable"}
    return {"status": "ok", "message": "Health endpoint responds"}


def diagnose(port: int = 8096) -> dict:
    engine = command_check(["docker", "info", "--format", "{{.ServerVersion}}"])
    report = {"docker_engine": engine, "application": http_check(port)}
    if engine["status"] != "ok":
        report["containers"] = {"status": "skipped", "message": "Docker Engine is unresponsive"}
        report["next_step"] = (
            "Inspect Docker Desktop diagnostics and other running workloads first. "
            "Do not restart the engine or delete volumes without assessing impact."
        )
        return report
    report["containers"] = command_check([
        "docker", "compose", "-f", str(ROOT / "compose.yaml"), "ps", "--all", "--format", "json"
    ])
    if report["application"]["status"] != "ok":
        report["next_step"] = (
            "Inspect app and migration logs with bounded timeouts. "
            "Verify DB health before app-only replacement. Never run compose down -v."
        )
    else:
        report["next_step"] = "Verify chat, workspace browsing, and diff proposal workflows."
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Non-destructive deployment diagnosis")
    parser.add_argument("--port", type=int, default=8096)
    options = parser.parse_args()
    if not 1 <= options.port <= 65535:
        parser.error("port must be 1 to 65535")
    result = diagnose(options.port)
    print(json.dumps(result, indent=2))
    return int(any(result[k]["status"] != "ok" for k in ("docker_engine", "application", "containers")))


if __name__ == "__main__":
    raise SystemExit(main())
