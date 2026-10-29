"""ComfyUI asynchronous bridge integration without GPU/model downloads."""
import httpx
import pytest

from jebat.features.image_gen.comfy_bridge import create_app
from jebat.features.image_gen.image_gen import ImageGenConfig, generate_image


@pytest.mark.asyncio
async def test_bridge_job_and_jebat_download(monkeypatch, tmp_path):
    token = "test-bridge-token"
    monkeypatch.setenv("JEBAT_COMFYUI_BRIDGE_TOKEN", token)
    monkeypatch.setenv("JEBAT_COMFYUI_BRIDGE", "1")
    monkeypatch.setenv("JEBAT_COMFYUI_CHECKPOINT", "local-test.safetensors")
    monkeypatch.setenv("JEBAT_COMFYUI_HOST", "http://bridge")
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    image_bytes = b"\x89PNG\r\n\x1a\nlocal-test-image"

    async def mock_handler(request):
        if request.url.path == "/jobs":
            return httpx.Response(202, json={"job_id": job_id, "status": "queued"})
        if request.url.path == f"/jobs/{job_id}":
            return httpx.Response(200, json={"job_id": job_id, "status": "completed"})
        if request.url.path == f"/jobs/{job_id}/result":
            return httpx.Response(200, json={"job_id": job_id, "status": "completed", "image_base64": __import__("base64").b64encode(image_bytes).decode(), "checkpoint": "local-test.safetensors", "prompt_id": "prompt-1"})
        if request.url.path == "/prompt":
            return httpx.Response(200, json={"prompt_id": "prompt-1"})
        if request.url.path == "/history/prompt-1":
            return httpx.Response(200, json={"prompt-1": {"outputs": {"9": {"images": [{"filename": "result.png", "subfolder": "", "type": "output"}]}}}})
        if request.url.path == "/view":
            return httpx.Response(200, content=image_bytes, headers={"content-type": "image/png"})
        raise AssertionError(request.url)
    app.state.client_factory = lambda *args, **kwargs: httpx.AsyncClient(transport=httpx.MockTransport(mock_handler), *args, **kwargs)
    async with httpx.AsyncClient(transport=transport, base_url="http://bridge") as client:
        rejected = await client.post("/jobs", json={"prompt": "test"})
        assert rejected.status_code == 401
        submitted = await client.post("/jobs", json={"prompt": "test"}, headers={"Authorization": f"Bearer {token}"})
        assert submitted.status_code == 202
        job_id = submitted.json()["job_id"]
        for _ in range(20):
            await __import__("asyncio").sleep(0.01)
            status = await client.get(f"/jobs/{job_id}", headers={"Authorization": f"Bearer {token}"})
            if status.json()["status"] == "completed":
                break
        assert status.json()["status"] == "completed", status.json()

    import jebat.features.image_gen.image_gen as image_module
    import httpx as caller_httpx
    caller_transport = caller_httpx.MockTransport(mock_handler)
    real_client = caller_httpx.AsyncClient
    image_module.httpx = caller_httpx
    caller_httpx.AsyncClient = lambda *args, **kwargs: real_client(transport=caller_transport, *args, **kwargs)
    result = await generate_image("test image", backend="comfyui", output_dir=str(tmp_path))
    assert result.success, result.error
    assert (tmp_path / f"comfyui-{job_id}.png").read_bytes() == image_bytes
