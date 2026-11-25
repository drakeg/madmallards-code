"""Initialize or rotate a database-backed administrator account.

Run after migrations: python -m app.bootstrap_admin --username admin
"""
import argparse
import re
import secrets

from sqlalchemy import select

from app.auth import PASSWORDS
from app.db import make_session_factory
from app.models import AuthSession, User


def bootstrap(username: str, *, rotate: bool = False) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,63}", username):
        raise ValueError("Username must contain 3-64 letters, numbers, periods, underscores, or hyphens")
    password = secrets.token_urlsafe(24)
    hashed = PASSWORDS.hash(password)
    with make_session_factory()() as db:
        user = db.scalar(select(User).where(User.username == username))
        if user and not rotate:
            raise ValueError("User already exists. Use --rotate to reset their password")
        if user:
            user.password_hash = hashed
            user.is_active = True
            user.is_admin = True
            db.query(AuthSession).filter(AuthSession.user_id == user.id).delete()
        else:
            db.add(User(username=username, password_hash=hashed, is_active=True, is_admin=True))
        db.commit()
    return password


def main() -> int:
    parser = argparse.ArgumentParser(description="Create/reset a MariaDB administrator login")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--rotate", action="store_true")
    options = parser.parse_args()
    try:
        password = bootstrap(options.username, rotate=options.rotate)
    except ValueError as exc:
        parser.exit(1, f"Account setup failed: {exc}\n")
    print("USERNAME=" + options.username)
    print("PASSWORD=" + password)
    print("Save this password securely. It will not be displayed again.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
