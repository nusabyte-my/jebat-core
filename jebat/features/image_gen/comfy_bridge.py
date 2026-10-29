"""Authenticated asynchronous bridge to a workstation ComfyUI server."""
from __future__ import annotations

import asyncio
import base64
import hmac
import os
import time
import uuid
from typing import Any, Dict

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    negative_prompt: str = Field(default="", max_length=4000)
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=1024, ge=256, le=2048)
    steps: int = Field(default=20, ge=1, le=100)
    cfg_scale: float = Field(default=7.0, ge=1, le=30)
    checkpoint: str | None = None
    seed: int | None = None


def create_app() -> FastAPI:
    app = FastAPI(title="JEBAT Local ComfyUI Bridge", docs_url=None, redoc_url=None)
    jobs: Dict[str, Dict[str, Any]] = {}
    client_factory = httpx.AsyncClient
    host = os.environ.get("COMFYUI_HOST", "http://127.0.0.1:8188").rstrip("/")
    token = os.environ.get("JEBAT_COMFYUI_BRIDGE_TOKEN", "")

    def authorize(authorization: str | None):
        if not token:
            raise HTTPException(503, "Bridge token is not configured")
        if not authorization or not hmac.compare_digest(authorization, f"Bearer {token}"):
            raise HTTPException(401, "Invalid bridge token")

    @app.get("/health")
    async def health():
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{host}/system_stats")
                response.raise_for_status()
                return {"status": "ok", "comfyui": "reachable", "system": response.json()}
        except Exception as exc:
            return {"status": "unavailable", "comfyui": "unreachable", "error": str(exc)}

    @app.post("/jobs", status_code=202)
    async def submit(request: GenerationRequest, authorization: str | None = Header(None)):
        authorize(authorization)
        job_id = uuid.uuid4().hex
        jobs[job_id] = {"job_id": job_id, "status": "queued", "created_at": time.time()}
        asyncio.create_task(run_job(job_id, request))
        return jobs[job_id]

    @app.get("/jobs/{job_id}")
    async def status(job_id: str, authorization: str | None = Header(None)):
        authorize(authorization)
        if job_id not in jobs:
            raise HTTPException(404, "Unknown job")
        return jobs[job_id]

    @app.get("/jobs/{job_id}/result")
    async def result(job_id: str, authorization: str | None = Header(None)):
        authorize(authorization)
        if job_id not in jobs:
            raise HTTPException(404, "Unknown job")
        job = jobs[job_id]
        if job["status"] != "completed":
            raise HTTPException(409, f"Job is {job['status']}")
        return job

    async def run_job(job_id: str, request: GenerationRequest):
        jobs[job_id]["status"] = "running"
        try:
            checkpoint = request.checkpoint or os.environ.get("JEBAT_COMFYUI_CHECKPOINT", "")
            if not checkpoint:
                raise RuntimeError("JEBAT_COMFYUI_CHECKPOINT is not configured")
            seed = request.seed if request.seed is not None else int.from_bytes(os.urandom(4), "big") % 2**31
            workflow = {
                "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": request.steps, "cfg": request.cfg_scale, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
                "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": checkpoint}},
                "5": {"class_type": "EmptyLatentImage", "inputs": {"width": request.width, "height": request.height, "batch_size": 1}},
                "6": {"class_type": "CLIPTextEncode", "inputs": {"text": request.prompt, "clip": ["4", 1]}},
                "7": {"class_type": "CLIPTextEncode", "inputs": {"text": request.negative_prompt, "clip": ["4", 1]}},
                "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
                "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "JEBAT", "images": ["8", 0]}},
            }
            timeout = httpx.Timeout(30, read=300)
            async with app.state.client_factory(timeout=timeout) as client:
                response = await client.post(f"{host}/prompt", json={"prompt": workflow})
                response.raise_for_status()
                prompt_id = response.json().get("prompt_id")
                jobs[job_id]["prompt_id"] = prompt_id
                for _ in range(150):
                    history = await client.get(f"{host}/history/{prompt_id}")
                    history.raise_for_status()
                    record = history.json().get(prompt_id, {})
                    if record:
                        outputs = record.get("outputs", {}).get("9", {}).get("images", [])
                        if not outputs:
                            raise RuntimeError("ComfyUI completed without an image")
                        info = outputs[0]
                        image = await client.get(f"{host}/view", params={"filename": info["filename"], "subfolder": info.get("subfolder", ""), "type": "output"})
                        image.raise_for_status()
                        jobs[job_id].update(status="completed", image_base64=base64.b64encode(image.content).decode("ascii"), mime_type=image.headers.get("content-type", "image/png"), seed=seed, checkpoint=checkpoint)
                        return
                    await asyncio.sleep(2)
                raise TimeoutError("ComfyUI generation timed out")
        except Exception as exc:
            jobs[job_id].update(status="failed", error=str(exc))

    app.state.client_factory = client_factory
    return app


app = create_app()
