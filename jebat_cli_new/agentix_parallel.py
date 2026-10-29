"""Bounded, observable parallel Agentix orchestration."""
from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jebat_cli_new.agentix_auto import _default_provider_id, _extract_json
from jebat_cli_new.agentix_llm import runs_dir
from jebat_cli_new.models import CompletionRequest

MAX_AGENTS = 3
READ_ONLY_TOOLS = {"read_file", "search_files", "list_dir"}


class ParallelOperationError(RuntimeError):
    pass


class ParallelCancelled(ParallelOperationError):
    pass


def _decompose(objective: str, workers: int, *, provider: str, model: str, registry) -> List[str]:
    impl = registry.get(provider)
    if impl is None:
        raise ParallelOperationError(f"provider {provider!r} is not configured; no fallback is permitted")
    prompt = (
        f"Split the objective into exactly {workers} independent, self-contained implementation or investigation slices. "
        "Each slice must have a distinct scope and must not require another slice's output. "
        "Do not assign two workers to edit the same file. Preserve the complete objective. "
        'Return only JSON: {"tasks": ["..."]}.\n\n'
        f"OBJECTIVE:\n{objective}"
    )
    try:
        response = impl.complete(CompletionRequest(provider=provider, model=model, prompt=prompt, temperature=0.2, max_tokens=4096))
        tasks = _extract_json(response.text or "")["tasks"]
        if not isinstance(tasks, list) or len(tasks) != workers:
            raise ValueError(f"expected {workers} tasks")
        tasks = [str(task).strip() for task in tasks]
        if any(not task for task in tasks):
            raise ValueError("empty task")
        return tasks
    except Exception as exc:
        raise ParallelOperationError(f"automatic decomposition failed on {provider}:{model}: {exc}; no model fallback is permitted") from exc


def operation_dir(run_id: str) -> Path:
    if not run_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in run_id):
        raise ParallelOperationError("invalid operation id")
    return runs_dir() / run_id


def cancel_operation(run_id: str) -> Dict[str, Any]:
    path = operation_dir(run_id) / "cancel"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(time.time()), encoding="utf-8")
    return {"run_id": run_id, "status": "cancellation_requested"}


def operation_status(run_id: str) -> Dict[str, Any]:
    state = operation_dir(run_id) / "state.json"
    if not state.is_file():
        raise ParallelOperationError(f"unknown parallel operation {run_id!r}")
    return json.loads(state.read_text(encoding="utf-8"))


class _Worktree:
    def __init__(self, root: Path):
        self.root = root
        self.path: Optional[Path] = None
        self.patch = ""

    def __enter__(self):
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=self.root, capture_output=True, text=True, check=False)
        if top.returncode:
            raise ParallelOperationError("parallel write mode requires a Git repository")
        self.path = Path(tempfile.mkdtemp(prefix="jebat-agentix-worktree-"))
        self.path.rmdir()
        result = subprocess.run(["git", "worktree", "add", "--detach", str(self.path), "HEAD"], cwd=top.stdout.strip(), capture_output=True, text=True, check=False)
        if result.returncode:
            raise ParallelOperationError(f"cannot create isolated worktree: {result.stderr.strip()}")
        return self.path

    def __exit__(self, *exc):
        if self.path:
            diff = subprocess.run(["git", "diff", "--binary", "HEAD"], cwd=self.path, capture_output=True, check=False)
            self.patch = diff.stdout.decode("utf-8", errors="replace")
            subprocess.run(["git", "worktree", "remove", "--force", str(self.path)], cwd=self.root, capture_output=True, check=False)
            if self.path.exists():
                shutil.rmtree(self.path, ignore_errors=True)


def run_parallel(
    sol: Path, objective: str, *, agents: int = MAX_AGENTS, yolo: bool = False,
    provider: Optional[str] = None, model: Optional[str] = None, verbose: bool = False,
    max_iterations: Optional[int] = None, registry=None, write: bool = False,
    deadline_seconds: Optional[float] = None, cancel_event: Optional[threading.Event] = None,
    run_id: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    from jebat_cli_new.agentix import _load_manifest
    from jebat_cli_new.agentix_llm import make_jailed_executor, run_with_agent_loop
    from jebat_cli_new.providers import ProviderRegistry

    if agents not in (2, 3):
        raise ParallelOperationError("agents must be 2 or 3")
    if deadline_seconds is not None and deadline_seconds <= 0:
        raise ParallelOperationError("deadline_seconds must be positive")
    registry = registry or ProviderRegistry()
    manifest = _load_manifest(sol)
    provider_name = provider or manifest.get("provider") or _default_provider_id(registry)
    if not provider_name:
        raise ParallelOperationError("no active provider configured; no fallback is permitted")
    model_name = model or manifest.get("model") or getattr(registry.configs.get(provider_name), "model", None) or "qwen2.5-coder:7b"
    tasks = _decompose(objective, agents, provider=provider_name, model=model_name, registry=registry)
    run_id = run_id or f"{time.strftime('%Y%m%d-%H%M%S')}-parallel-{manifest['name']}-{uuid.uuid4().hex[:4]}"
    trace_id = uuid.uuid4().hex
    record_dir = runs_dir() / run_id
    record_dir.mkdir(parents=True, exist_ok=False)
    cancel_path = record_dir / "cancel"
    started = time.monotonic()
    deadline = started + deadline_seconds if deadline_seconds else None
    lock = threading.Lock()
    state: Dict[str, Any] = {
        "run_id": run_id, "trace_id": trace_id, "status": "running", "provider": provider_name,
        "model": model_name, "write_mode": write, "deadline_seconds": deadline_seconds,
        "workers": [{"worker": i + 1, "task": task, "status": "queued"} for i, task in enumerate(tasks)],
    }

    def save():
        with lock:
            (record_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    (record_dir / "brief.json").write_text(json.dumps({**state, "solution": manifest["name"], "objective": objective}, indent=2), encoding="utf-8")
    save()

    def work(item):
        index, task = item
        if cancel_event and cancel_event.is_set() or cancel_path.exists():
            raise ParallelCancelled(f"worker {index + 1} cancelled")
        with lock:
            state["workers"][index]["status"] = "running"
            state["workers"][index]["started_at"] = time.time()
        save()
        scoped = (
            f"PARALLEL OPERATION — worker {index + 1}/{agents}. Trace: {trace_id}\n"
            f"Overall objective: {objective}\nYour exclusive slice: {task}\n"
            "Complete only this slice. Do not edit files assigned to another slice. "
            "Report concrete results and any remaining blocker."
        )
        workspace_manager = _Worktree(sol) if write else _null_workspace(sol)
        with workspace_manager as workspace:
            policy = dict(manifest)
            if write:
                policy["llm_workspace"] = "."
                tool_executor = make_jailed_executor(policy, sol, workspace_override=workspace)
            else:
                policy["llm_tools"] = sorted(READ_ONLY_TOOLS)
                tool_executor = make_jailed_executor(policy, sol)
            answer, info = run_with_agent_loop(
                sol, scoped, yolo=yolo, provider=provider_name, model=model_name,
                verbose=verbose, max_iterations=max_iterations, registry=registry,
                record_dir=record_dir / "workers", workspace_override=workspace if write else None,
                tool_executor=tool_executor,
            )
        if write and workspace_manager.patch:
            patch_path = record_dir / f"worker-{index + 1}.patch"
            patch_path.write_text(workspace_manager.patch, encoding="utf-8")
            info["patch"] = str(patch_path)
        if not answer or answer.startswith("[JEBAT provider error:"):
            raise ParallelOperationError(answer or "worker returned no answer")
        with lock:
            state["workers"][index].update(status="completed", run_id=info["run_id"], finished_at=time.time())
        save()
        return {"worker": index + 1, "task": task, "answer": answer, "info": info}

    class _null_workspace:
        def __init__(self, path): self.path = path
        def __enter__(self): return self.path
        def __exit__(self, *exc): pass

    with concurrent.futures.ThreadPoolExecutor(max_workers=agents) as pool:
        futures = {pool.submit(work, item): item[0] for item in enumerate(tasks)}
        outcomes = []
        pending = set(futures)
        while pending:
            if cancel_event and cancel_event.is_set() or cancel_path.exists():
                for future in pending:
                    future.cancel()
                state["status"] = "cancelled"
                save()
                raise ParallelCancelled(f"operation {run_id} cancelled")
            if deadline and time.monotonic() >= deadline:
                for future in pending:
                    future.cancel()
                state["status"] = "deadline_exceeded"
                save()
                raise ParallelOperationError(f"operation {run_id} exceeded {deadline_seconds}s deadline")
            done, pending = concurrent.futures.wait(pending, timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                index = futures[future]
                try:
                    outcomes.append((index, future.result()))
                except Exception as exc:
                    for other in pending:
                        other.cancel()
                    with lock:
                        state["workers"][index].update(status="failed", error=str(exc))
                        state["status"] = "failed"
                    save()
                    (record_dir / "failed.json").write_text(json.dumps({"worker": index + 1, "error": str(exc)}, indent=2), encoding="utf-8")
                    raise ParallelOperationError(f"worker {index + 1} failed on {provider_name}:{model_name}: {exc}") from exc

    outcomes.sort()
    results = [item[1] for item in outcomes]
    payload = {
        "run_id": run_id, "trace_id": trace_id, "provider": provider_name, "model": model_name,
        "agents": agents, "status": "completed", "tasks": tasks,
        "workers": [{"worker": o["worker"], "task": o["task"], "answer": o["answer"], **o["info"]} for o in results],
        "tokens": sum(o["info"].get("tokens", 0) for o in results),
        "tool_calls": sum(o["info"].get("tool_calls", 0) for o in results),
    }
    state["status"] = "completed"
    save()
    (record_dir / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [f"Parallel operation: {manifest['name']} · {provider_name}:{model_name} · {agents} agents", ""]
    for result in results:
        lines += [f"## Worker {result['worker']} — {result['task']}", result["answer"], ""]
    text = "\n".join(lines).strip()
    (record_dir / "result.md").write_text(text + "\n", encoding="utf-8")
    return text, payload
