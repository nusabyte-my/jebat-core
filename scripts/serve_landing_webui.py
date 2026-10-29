"""Serve the landing page and real JEBAT WebUI on one local port."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from jebat.services.webui.webui_server import _mount_static, webui_router
from jebat.services.webui.builder import router as builder_router

app = FastAPI(title="JEBAT Local")
app.include_router(webui_router)
app.include_router(builder_router)
_mount_static(app)

from jebat.services.webui.builder import root as builder_root
(builder_root() / "deployments").mkdir(parents=True, exist_ok=True)
app.mount("/builder", StaticFiles(directory=str(builder_root()), html=True), name="builder-preview")
app.mount("/deployments", StaticFiles(directory=str(builder_root() / "deployments"), html=True), name="preview-deployments")

# Landing page and public assets, after API routes.
app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parents[1]), html=True), name="landing")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=4173)
