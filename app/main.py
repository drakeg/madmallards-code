from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.ai_proposals import router as ai_proposal_router
from app.api_models import router as models_router
from app.auth import authenticated
from app.auth import router as auth_router
from app.conversations import router as conversations_router
from app.github_status import router as github_router
from app.workspaces import router as workspaces_router

app = FastAPI(title="Mad Mallards Code", version="0.1.0")


@app.middleware("http")
async def require_login(request: Request, call_next):
    # Docker health probes are intentionally unauthenticated.
    if request.url.path == "/health" or request.url.path in {"/auth/login", "/favicon.ico"}:
        return await call_next(request)
    if not authenticated(request):
        if request.url.path.startswith("/api/") or request.method != "GET":
            return JSONResponse({"detail": "Authentication required"}, status_code=401)
        return RedirectResponse("/auth/login", status_code=303)
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin:
            from urllib.parse import urlsplit
            if urlsplit(origin).netloc != request.headers.get("host"):
                return JSONResponse({"detail": "Invalid request origin"}, status_code=403)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


app.include_router(auth_router)
app.include_router(models_router)
app.include_router(ai_proposal_router)
app.include_router(github_router)
app.include_router(conversations_router)
app.include_router(workspaces_router)
app.mount('/static', StaticFiles(directory=str(Path(__file__).parent / 'static')), name='static')
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/info")
def info() -> dict[str, str]:
    return {"name": "Mad Mallards Code", "version": "0.1.0", "phase": "foundation"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"project": "Mad Mallards Code"})
