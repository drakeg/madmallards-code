"""Database-backed user identity and revocable login sessions."""
import hashlib
import os
import secrets
import time
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.db import make_session_factory
from app.models import AuthSession, User

router = APIRouter()
COOKIE = "mmc_session"
SESSION_SECONDS = 8 * 60 * 60
FAILED_ATTEMPTS = defaultdict(deque)
PASSWORDS = PasswordHash.recommended()
# Run a costly dummy verification for unknown users to reduce timing differences.
DUMMY_HASH = PASSWORDS.hash("a-nonexistent-password-for-timing")


@lru_cache(maxsize=1)
def auth_session_factory() -> sessionmaker:
    return make_session_factory()


def utc_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def authenticated(request: Request) -> bool:
    token = request.cookies.get(COOKIE)
    if not token or len(token) > 256:
        return False
    try:
        with auth_session_factory()() as db:
            session = db.scalar(
                select(AuthSession)
                .join(User)
                .where(
                    AuthSession.token_hash == token_digest(token),
                    AuthSession.expires_at > utc_naive(),
                    User.is_active.is_(True),
                )
            )
            return session is not None
    except SQLAlchemyError:
        return False


def login_page() -> HTMLResponse:
    return HTMLResponse(
        """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign in — Mad Mallards Code</title>
<style>body{font:16px system-ui,sans-serif;background:#172134;color:#202c3e;
display:grid;min-height:100vh;place-items:center;margin:0;padding:18px;box-sizing:border-box}
main{background:white;border-radius:14px;padding:32px;width:min(100%,410px);
box-shadow:0 18px 60px #09101c80}h1{font-size:1.5rem}
input,button{box-sizing:border-box;width:100%;font:inherit;border-radius:8px;
padding:12px;margin:10px 0}input{border:1px solid #a5b0c2}
button{background:#145bd7;color:white;border:0;cursor:pointer}
small{color:#5b6779}#status{color:#a32121;min-height:1.4em}</style></head>
<body><main><h1>Mad Mallards Code</h1><p>Sign in to your account.</p>
<form id="login">
<label for="username">Username</label>
<input id="username" name="username" autocomplete="username" maxlength="64" required autofocus>
<label for="password">Password</label>
<input id="password" type="password" autocomplete="current-password" required>
<button type="submit">Sign in</button></form>
<p id="status" role="alert"></p><small>Trusted local networks only. HTTP does not encrypt login traffic.
Do not expose this service to the internet.</small></main>
<script>
document.getElementById('login').addEventListener('submit',async event=>{
event.preventDefault();const button=document.querySelector('button');button.disabled=true;
try{const response=await fetch('/auth/login',{method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({username:document.getElementById('username').value,
password:document.getElementById('password').value})});
document.getElementById('password').value='';
if(!response.ok){document.getElementById('status').textContent=
response.status===429?'Too many attempts. Try again later.':'Invalid username or password';return;}
window.location.replace('/');
}catch(_){document.getElementById('status').textContent='Unable to connect';}
finally{button.disabled=false;}
});
</script></body></html>""",
        status_code=200,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/auth/login", response_class=HTMLResponse)
def login_form(request: Request):
    if authenticated(request):
        return RedirectResponse("/", status_code=303)
    return login_page()


@router.post("/auth/login")
async def login(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    failures = FAILED_ATTEMPTS[ip]
    while failures and now - failures[0] > 60:
        failures.popleft()
    if len(failures) >= 5:
        return JSONResponse({"detail": "Too many attempts"}, status_code=429)
    try:
        data = await request.json()
        username = data.get("username", "")
        password = data.get("password", "")
    except (ValueError, AttributeError, TypeError):
        username, password = "", ""
    if (not isinstance(username, str) or not isinstance(password, str)
            or len(username) > 64 or len(password) > 1024):
        failures.append(now)
        return JSONResponse({"detail": "Invalid credentials"}, status_code=401)
    try:
        with auth_session_factory()() as db:
            user = db.scalar(select(User).where(User.username == username))
            verified = PASSWORDS.verify(password, user.password_hash if user else DUMMY_HASH)
            if not user or not user.is_active or not verified:
                failures.append(now)
                return JSONResponse({"detail": "Invalid credentials"}, status_code=401)
            token = secrets.token_urlsafe(48)
            session = AuthSession(
                user_id=user.id,
                token_hash=token_digest(token),
                expires_at=utc_naive() + timedelta(seconds=SESSION_SECONDS),
            )
            db.add(session)
            db.commit()
    except SQLAlchemyError:
        return JSONResponse({"detail": "Database authentication unavailable"}, status_code=503)
    failures.clear()
    response = JSONResponse({"authenticated": True, "username": username})
    response.set_cookie(
        COOKIE, token, httponly=True, samesite="strict",
        secure=os.environ.get("APP_COOKIE_SECURE") == "1",
        max_age=SESSION_SECONDS, path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/auth/logout")
def logout(request: Request):
    token = request.cookies.get(COOKIE)
    if token:
        try:
            with auth_session_factory()() as db:
                record = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_digest(token)))
                if record is not None:
                    db.delete(record)
                    db.commit()
        except SQLAlchemyError:
            return JSONResponse({"detail": "Logout unavailable"}, status_code=503)
    response = JSONResponse({"authenticated": False})
    response.delete_cookie(COOKIE, path="/", samesite="strict")
    response.headers["Cache-Control"] = "no-store"
    return response
