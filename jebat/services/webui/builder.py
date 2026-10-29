"""HangNadim Builder project workspace, checkpoints, preview, and export."""
from __future__ import annotations

import json
import os
import shutil
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/webui/api/builder", tags=["builder"])
PROJECTS: Dict[str, Dict[str, Any]] = {}


def root() -> Path:
    path = Path(os.environ.get("JEBAT_BUILDER_DIR", Path.home() / ".jebat" / "builder")).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_path(project_id: str) -> Path:
    if not project_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in project_id):
        raise HTTPException(400, "Invalid project id")
    path = (root() / project_id).resolve()
    if root() not in path.parents:
        raise HTTPException(400, "Invalid project path")
    return path


def safe_file(project_id: str, relative: str) -> Path:
    target = (project_path(project_id) / relative).resolve()
    if project_path(project_id) not in target.parents:
        raise HTTPException(400, "Path escapes project")
    return target


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    objective: str = Field(min_length=1, max_length=4000)


class FileUpdate(BaseModel):
    content: str = Field(max_length=500000)


class BuilderAction(BaseModel):
    action: str
    instruction: str = Field(default="", max_length=4000)


class ImplementRequest(BaseModel):
    provider: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=255)


class DeployRequest(BaseModel):
    confirm: bool = False


def _extract_json(text: str) -> Dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("model returned no JSON object")
    return json.loads(text[start:end + 1])


def initial_html(name: str, objective: str) -> str:
    import html
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(name)}</title><link rel="stylesheet" href="styles.css"></head><body><main data-component="app"><p>HangNadim project</p><h1 data-component="title">{html.escape(name)}</h1><p id="objective">{html.escape(objective)}</p><button id="action" data-component="primary-action">Run first action</button><p class="status" id="status">Preview is live. Edit index.html to iterate.</p></main><script src="app.js"></script></body></html>"""


def initial_css() -> str:
    return """body{font-family:system-ui;max-width:860px;margin:64px auto;padding:24px;color:#17201b;background:#f5f5f2}main{background:white;padding:32px;border:1px solid #d9ddd6;border-radius:8px}button{padding:12px 18px;background:#276749;color:white;border:0;border-radius:4px}.status{color:#69716b}"""


def initial_js() -> str:
    return """document.getElementById('action').addEventListener('click',()=>document.getElementById('status').textContent='Action completed.');"""


def project_plan(name: str, objective: str) -> Dict[str, Any]:
    return {"name": name, "objective": objective, "pages": [{"name": "Overview", "artifact": "index.html"}], "components": [{"name": "Project title", "selector": "[data-component='title']"}, {"name": "Primary action", "selector": "[data-component='primary-action']"}], "files": ["index.html", "styles.css", "app.js"], "checks": ["Preview loads", "Primary action changes status"]}


def checkpoint(project_id: str, label: str) -> Dict[str, Any]:
    project = project_path(project_id)
    checkpoint_id = f"{int(time.time())}-{uuid.uuid4().hex[:5]}"
    target = project / ".checkpoints" / checkpoint_id
    target.mkdir(parents=True)
    for file in project.glob("*.html"):
        shutil.copy2(file, target / file.name)
    manifest = {"id": checkpoint_id, "label": label, "created_at": time.time()}
    (target / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


@router.post("/projects")
def create_project(payload: ProjectCreate):
    project_id = uuid.uuid4().hex[:12]
    path = project_path(project_id)
    path.mkdir()
    (path / "index.html").write_text(initial_html(payload.name, payload.objective), encoding="utf-8")
    (path / "styles.css").write_text(initial_css(), encoding="utf-8")
    (path / "app.js").write_text(initial_js(), encoding="utf-8")
    (path / "plan.json").write_text(json.dumps(project_plan(payload.name, payload.objective), indent=2), encoding="utf-8")
    (path / "project.json").write_text(json.dumps({"id": project_id, "name": payload.name, "objective": payload.objective}, indent=2), encoding="utf-8")
    checkpoint(project_id, "Initial project")
    return {"id": project_id, "name": payload.name, "preview": f"/builder/{project_id}/index.html", "files": ["index.html", "styles.css", "app.js"], "plan": project_plan(payload.name, payload.objective)}


@router.post("/projects/{project_id}/implement")
def implement_project(project_id: str, payload: ImplementRequest):
    project = project_path(project_id)
    metadata = json.loads((project / "project.json").read_text(encoding="utf-8"))
    from jebat_cli_new.agentix_auto import _default_provider_id
    from jebat_cli_new.models import CompletionRequest
    from jebat_cli_new.providers import ProviderRegistry
    registry = ProviderRegistry()
    provider = payload.provider or _default_provider_id(registry)
    if not provider or not registry.get(provider):
        return {"status": "unavailable", "error": "No configured provider; project plan and deterministic files retained"}
    model = payload.model or getattr(registry.configs.get(provider), "model", "")
    prompt = (
        "Implement a self-contained three-file static web app from the project plan. "
        "Return JSON with keys index.html, styles.css, app.js. Include data-component attributes "
        "for visual source targeting. No external scripts, credentials, or build step.\n"
        f"Plan: {json.dumps(project_plan(metadata['name'], metadata['objective']))}"
    )
    try:
        response = registry.get(provider).complete(CompletionRequest(provider=provider, model=model, prompt=prompt, max_tokens=8192))
        files = _extract_json(response.text)
        for filename in ("index.html", "styles.css", "app.js"):
            content = files[filename]
            if not isinstance(content, str) or not content.strip():
                raise ValueError(f"missing {filename}")
            (project / filename).write_text(content, encoding="utf-8")
        checkpoint(project_id, "Agent implementation")
        return {"status": "implemented", "provider": provider, "model": model, "files": ["index.html", "styles.css", "app.js"]}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


@router.post("/projects/{project_id}/test")
def test_project(project_id: str):
    from html.parser import HTMLParser
    project = project_path(project_id)
    source = (project / "index.html").read_text(encoding="utf-8")
    parser = HTMLParser()
    try:
        parser.feed(source)
        parser.close()
        html_ok = True
    except Exception as exc:
        return {"status": "failed", "checks": [{"name": "HTML parse", "status": "failed", "detail": str(exc)}]}
    checks = [
        {"name": "HTML parse", "status": "passed" if html_ok else "failed"},
        {"name": "Primary action", "status": "passed" if 'id="action"' in source else "failed"},
        {"name": "Visual source targets", "status": "passed" if "data-component" in source else "failed"},
        {"name": "Stylesheet", "status": "passed" if (project / "styles.css").is_file() else "failed"},
        {"name": "Script", "status": "passed" if (project / "app.js").is_file() else "failed"},
    ]
    return {"status": "passed" if all(c["status"] == "passed" for c in checks) else "failed", "checks": checks}


@router.post("/projects/{project_id}/deploy")
def deploy_project(project_id: str, payload: DeployRequest):
    if not payload.confirm:
        return {"status": "confirmation_required", "message": "Deployment publishes the project preview. Retry with confirm=true after reviewing the project and tests."}
    project = project_path(project_id)
    target = root() / "deployments" / project_id
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(project, target, ignore=shutil.ignore_patterns(".checkpoints"))
    (project / "deployment.json").write_text(json.dumps({"project_id": project_id, "url": f"/deployments/{project_id}/index.html", "status": "preview_deployed"}, indent=2), encoding="utf-8")
    return {"status": "preview_deployed", "url": f"/deployments/{project_id}/index.html"}


@router.post("/projects/{project_id}/rollback")
def rollback_deployment(project_id: str):
    target = root() / "deployments" / project_id
    if target.exists():
        shutil.rmtree(target)
    return {"status": "rolled_back"}


@router.get("/projects/{project_id}/media")
def project_media(project_id: str):
    project = project_path(project_id)
    media = []
    for path in project.rglob("*"):
        if not path.is_file() or ".checkpoints" in path.parts:
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".glb"}:
            item = {"name": path.name, "url": f"/builder/{project_id}/{path.relative_to(project).as_posix()}"}
            if path.suffix.lower() == ".glb":
                item["content"] = f"{path.stat().st_size} bytes"
            media.append(item)
    return {"artifacts": media}


@router.get("/projects/{project_id}/plan")
def get_plan(project_id: str):
    path = safe_file(project_id, "plan.json")
    if not path.is_file():
        raise HTTPException(404, "Project plan not found")
    return json.loads(path.read_text(encoding="utf-8"))


@router.post("/projects/{project_id}/fork")
def fork_project(project_id: str):
    source = project_path(project_id)
    if not source.is_dir():
        raise HTTPException(404, "Project not found")
    fork_id = uuid.uuid4().hex[:12]
    target = project_path(fork_id)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(".checkpoints")
    )
    metadata = json.loads((target / "project.json").read_text(encoding="utf-8"))
    metadata.update(id=fork_id, name=f"{metadata['name']} (Fork)", forked_from=project_id)
    (target / "project.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    checkpoint(fork_id, "Forked project")
    return {"id": fork_id, "name": metadata["name"], "preview": f"/builder/{fork_id}/index.html", "files": ["index.html", "styles.css", "app.js"]}


@router.get("/projects/{project_id}/files/{file_path:path}")
def read_file(project_id: str, file_path: str):
    path = safe_file(project_id, file_path)
    if not path.is_file():
        raise HTTPException(404, "File not found")
    return {"path": file_path, "content": path.read_text(encoding="utf-8")}


@router.put("/projects/{project_id}/files/{file_path:path}")
def update_file(project_id: str, file_path: str, payload: FileUpdate):
    path = safe_file(project_id, file_path)
    if path.suffix not in {".html", ".css", ".js", ".json", ".md"}:
        raise HTTPException(400, "Unsupported file type")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload.content, encoding="utf-8")
    checkpoint(project_id, "Edited project")
    return {"status": "saved", "path": file_path}


@router.get("/projects/{project_id}/checkpoints")
def checkpoints(project_id: str):
    base = project_path(project_id) / ".checkpoints"
    records = []
    if base.is_dir():
        for path in sorted(base.iterdir(), reverse=True):
            if (path / "manifest.json").is_file():
                records.append(json.loads((path / "manifest.json").read_text(encoding="utf-8")))
    return {"checkpoints": records}


@router.post("/projects/{project_id}/checkpoints/{checkpoint_id}/restore")
def restore_checkpoint(project_id: str, checkpoint_id: str):
    source = safe_file(project_id, f".checkpoints/{checkpoint_id}")
    if not source.is_dir():
        raise HTTPException(404, "Checkpoint not found")
    for file in source.glob("*.html"):
        shutil.copy2(file, project_path(project_id) / file.name)
    return {"status": "restored", "checkpoint": checkpoint_id}


@router.get("/projects/{project_id}/export")
def export_project(project_id: str):
    project = project_path(project_id)
    archive = root() / f"{project_id}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for file in project.rglob("*"):
            if file.is_file() and ".checkpoints" not in file.parts:
                bundle.write(file, file.relative_to(project))
    return FileResponse(archive, filename=f"hangnadim-{project_id}.zip")
