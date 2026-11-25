"""Configure a single-user LAN login without committing secrets.

Run from the repository: python3 scripts/setup_access.py
"""
import argparse
import os
import secrets
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS = {"APP_ACCESS_PASSWORD", "APP_SESSION_SECRET", "APP_COOKIE_SECURE"}


def setup(env_path: Path, *, rotate: bool = False) -> str:
    if env_path.is_symlink():
        raise ValueError("Refusing to edit a symlink")
    if not env_path.is_file():
        raise FileNotFoundError("Create the local .env from .env.example first")
    original = env_path.read_text(encoding="utf-8")
    existing = {
        line.split("=", 1)[0]
        for line in original.splitlines()
        if "=" in line and not line.startswith("#")
    }
    if "APP_ACCESS_PASSWORD" in existing and not rotate:
        raise ValueError("Access is already configured; use --rotate to replace credentials")
    password = secrets.token_urlsafe(24)
    secret = secrets.token_urlsafe(48)
    preserved = [
        line for line in original.splitlines()
        if line.split("=", 1)[0] not in KEYS
    ]
    updated = "\n".join(preserved).rstrip("\n") + (
        f"\nAPP_ACCESS_PASSWORD={password}"
        f"\nAPP_SESSION_SECRET={secret}"
        "\nAPP_COOKIE_SECURE=0\n"
    )
    fd, temp_name = tempfile.mkstemp(prefix=".mmc-auth-", dir=env_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            os.fchmod(output.fileno(), 0o600)
            output.write(updated)
        os.replace(temp_name, env_path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return password


def main() -> int:
    parser = argparse.ArgumentParser(description="Set up local LAN access credentials")
    parser.add_argument("--rotate", action="store_true", help="Replace existing credentials; signs out all sessions")
    args = parser.parse_args()
    try:
        password = setup(ROOT / ".env", rotate=args.rotate)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Unable to configure access: {exc}\n")
    print("Access password (save it securely; it will not be displayed again):")
    print(password)
    print("Credentials stored in ignored .env with file permissions 0600.")
    print("Deploy with: docker compose up -d --build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
