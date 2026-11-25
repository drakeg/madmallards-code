"""Single-user password login for trusted-LAN development deployments."""
import hmac
import os
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

router = APIRouter()
COOKIE = "mmc_session"
SESSION_SECONDS = 8 * 60 * 60
FAILED_ATTEMPTS = defaultdict(deque)


def configured() -> bool:
    return len(os.environ.get("APP_ACCESS_PASSWORD", "")) >= 16 and len(
        os.environ.get("APP_SESSION_SECRET", "")
    ) >= 32


def signer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(os.environ["APP_SESSION_SECRET"], salt="mmc-local-session-v1")


def authenticated(request: Request) -> bool:
    token = request.cookies.get(COOKIE)
    if not token or not configured():
        return False
    try:
        payload = signer().loads(token, max_age=SESSION_SECONDS)
        return payload == {"v": 1}
    except (BadSignature, SignatureExpired):
        return False


def login_page(message: str = "") -> HTMLResponse:
    # The message is always an internal constant, never user-supplied HTML.
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
<body><main><h1>Mad Mallards Code</h1><p>Enter the LAN access password.</p>
<form id="login"><label for="password">Password</label>
<input id="password" type="password" autocomplete="current-password" required autofocus>
<button type="submit">Sign in</button></form>
<p id="status" role="alert"></p><small>Trusted local networks only. Do not expose this
HTTP service to the internet.</small></main>
<script>
document.getElementById('login').addEventListener('submit',async event=>{
event.preventDefault();const button=document.querySelector('button');button.disabled=true;
try{const response=await fetch('/auth/login',{method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({password:document.getElementById('password').value})});
document.getElementById('password').value='';
if(!response.ok){document.getElementById('status').textContent=
response.status===429?'Too many attempts. Try again later.':'Invalid password';return;}
window.location.replace('/');
}catch(_){document.getElementById('status').textContent='Unable to connect';}
finally{button.disabled=false;}
});
</script></body></html>"""
    , status_code=200, headers={"Cache-Control": "no-store"})


@router.get("/auth/login", response_class=HTMLResponse)
def login_form(request: Request):
    if authenticated(request):
        return RedirectResponse("/", status_code=303)
    return login_page()


@router.post("/auth/login")
async def login(request: Request):
    if not configured():
        return JSONResponse({"detail": "Server authentication is not configured"}, status_code=503)
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    failures = FAILED_ATTEMPTS[ip]
    while failures and now - failures[0] > 60:
        failures.popleft()
    if len(failures) >= 5:
        return JSONResponse({"detail": "Too many attempts"}, status_code=429)
    try:
        data = await request.json()
        password = data.get("password", "")
    except (ValueError, AttributeError, TypeError):
        password = ""
    if not isinstance(password, str) or not hmac.compare_digest(
        password.encode(), os.environ["APP_ACCESS_PASSWORD"].encode()
    ):
        failures.append(now)
        return JSONResponse({"detail": "Invalid credentials"}, status_code=401)
    failures.clear()
    response = JSONResponse({"authenticated": True})
    response.set_cookie(
        COOKIE, signer().dumps({"v": 1}), httponly=True, samesite="strict",
        secure=os.environ.get("APP_COOKIE_SECURE") == "1",
        max_age=SESSION_SECONDS, path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/auth/logout")
def logout():
    response = JSONResponse({"authenticated": False})
    response.delete_cookie(COOKIE, path="/", samesite="strict")
    response.headers["Cache-Control"] = "no-store"
    return response
