from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api_models import router as models_router
from app.conversations import router as conversations_router
from app.workspaces import router as workspaces_router

app = FastAPI(title="Mad Mallards Code", version="0.1.0")
app.include_router(models_router)
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
