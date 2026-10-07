"""Run: python scripts/check_workflows.py. Isolated, no model calls or deployments."""

from __future__ import annotations

import asyncio
import json
import os
import socket
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def command(*args: str, stdin: str = "", ok: bool = True):
    result = subprocess.run(
        [sys.executable, "-m", "jebat_cli_new", *args], input=stdin,
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    if ok:
        assert result.returncode == 0, (args, result.stdout, result.stderr)
    return result


async def check_memory():
    from jebat.features.memory import EnhancedMemorySystem, MemoryType
    from jebat.tools import automimpi_tools as tools

    memory = EnhancedMemorySystem(storage_path=Path.home() / "isolated-memory")
    project = Path.cwd().name
    own = await memory.encode(
        f"[{project}][stack] current fact", memory_type=MemoryType.SEMANTIC,
        tags={"project", f"project:{project}"},
    )
    foreign = await memory.encode(
        "[elsewhere][stack] private foreign fact", memory_type=MemoryType.SEMANTIC,
        tags={"project", "project:elsewhere"},
    )
    with patch.object(tools, "_memory", memory):
        recalled = await tools.project_recall()
        assert [fact["memory_id"] for fact in recalled["facts"]] == [own.trace_id]
        assert Path(recalled["project_root"]) == Path.cwd()
        assert (await tools.project_forget(foreign.trace_id))["status"] == "not_found"
        assert foreign.trace_id in memory.traces
        await tools.session_learning_commit("handoff", ["durable workflow boundary"])
        recalled = await tools.project_recall(query="durable workflow boundary")
        assert [fact["content"] for fact in recalled["facts"]] == ["durable workflow boundary"]
        assert (await tools.project_forget(own.trace_id))["status"] == "deleted"
    persisted = EnhancedMemorySystem(storage_path=memory.storage_path)
    assert own.trace_id not in persisted.traces
    assert foreign.trace_id in persisted.traces
    print("PASS project recall, deletion boundary, handoff persistence")


async def check_engine():
    from jebat.orchestration.workflow_engine import WorkflowEngine, TaskStatus, WorkflowStatus

    engine = WorkflowEngine()
    workflow = engine.create_workflow("repeat")
    same_name = engine.create_workflow("repeat")
    assert workflow.id != same_name.id
    values = iter([7, 11])
    engine.add_task(workflow.id, "source", "Source", lambda: next(values))
    consumer = engine.add_task(workflow.id, "consumer", "Consumer", lambda **kw: kw["_source_result"] * 2, dependencies=["source"])
    first = await engine.execute_workflow(workflow.id)
    second = await engine.execute_workflow(workflow.id)
    assert first["results"] == {"source": 7, "consumer": 14}
    assert second["results"] == {"source": 11, "consumer": 22}
    assert first["execution_id"] != second["execution_id"]
    assert consumer.kwargs == {}
    try:
        engine.add_task(workflow.id, "source", "Replacement", lambda: 99)
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate task replaced the original")

    broken = engine.create_workflow("failure")
    # Reverse insertion order must not strand descendants in PENDING.
    engine.add_task(broken.id, "leaf", "Leaf", lambda: 1, dependencies=["middle"])
    engine.add_task(broken.id, "middle", "Middle", lambda: 1, dependencies=["root"])
    def fail():
        raise RuntimeError("expected failure")
    engine.add_task(broken.id, "root", "Root", fail)
    result = await engine.execute_workflow(broken.id)
    assert result["status"] == "failed" and result["failed_tasks"] == 1
    assert result["skipped_tasks"] == 2
    assert broken.tasks["leaf"].status == TaskStatus.SKIPPED

    cancelled = engine.create_workflow("cancel")
    started, release = asyncio.Event(), asyncio.Event()
    async def hold():
        started.set()
        await release.wait()
        return "released"
    engine.add_task(cancelled.id, "hold", "Hold", hold)
    running = asyncio.create_task(engine.execute_workflow(cancelled.id))
    await started.wait()
    assert "error" in await engine.execute_workflow(cancelled.id)
    running.cancel()
    try:
        await running
    except asyncio.CancelledError:
        pass
    assert cancelled.status == WorkflowStatus.FAILED
    assert cancelled.tasks["hold"].status == TaskStatus.CANCELLED
    release.set()
    assert (await engine.execute_workflow(cancelled.id))["results"]["hold"] == "released"
    print("PASS DAG rerun, fresh results, unique runs, failure propagation, cancellation")


def check_dream():
    import jebat_cli_new.jebat as cli
    from jebat.features.memory.automimpi import load_dream_state, save_dream_state

    old = "2020-01-01T00:00:00+00:00"
    save_dream_state({"dream_count": 8, "sessions_since_dream": 4, "last_dream": old})
    with patch.object(cli, "_run_dream", return_value=None):
        cli._auto_mimpi_check(None)
    assert load_dream_state() == {"dream_count": 8, "sessions_since_dream": 5, "last_dream": old}
    recent = datetime.now(timezone.utc).isoformat()
    save_dream_state({"dream_count": 8, "sessions_since_dream": 4, "last_dream": recent})
    with patch.object(cli, "_run_dream", side_effect=AssertionError("cooldown bypassed")):
        cli._auto_mimpi_check(None)
    assert load_dream_state()["dream_count"] == 8
    assert load_dream_state()["sessions_since_dream"] == 5
    # Run the real consolidation against the isolated, empty home store.
    save_dream_state({"dream_count": 8, "sessions_since_dream": 4, "last_dream": old})
    cli._auto_mimpi_check(None)
    after = load_dream_state()
    assert after["dream_count"] == 9 and after["sessions_since_dream"] == 0
    assert datetime.fromisoformat(after["last_dream"]) > datetime.now(timezone.utc) - timedelta(minutes=1)
    print("PASS dream failure accounting, cooldown, real successful consolidation")


def check_cli():
    import jebat_cli_new.jebat as cli

    original = [{"role": "user", "content": "retained objective"}, {"role": "assistant", "content": "retained decision"}]
    session = cli.SESSIONS_DIR / "session_20200101_000000.json"
    session.write_text(json.dumps(original), encoding="utf-8")
    for args in (("repl", "--session", session.stem), ("--session", session.stem), ("--continue",)):
        before = set(cli.SESSIONS_DIR.glob("*.json"))
        command(*args, stdin="!echo CONTINUATION_PROOF\n/exit\n")
        created = set(cli.SESSIONS_DIR.glob("*.json")) - before
        assert len(created) == 1
        messages = json.loads(created.pop().read_text(encoding="utf-8"))
        assert messages[:2] == original
        assert "CONTINUATION_PROOF" in messages[-1]["content"]
    assert command("repl", "--session", "absent", ok=False).returncode == 1
    assert command("--session", ok=False).returncode == 2
    db = cli.TaskDB()
    try:
        saved = Path(db.save_session([cli.AgentMessage(role="user", content="manual save")]))
        assert cli._load_session_by_id(saved.stem)[0].content == "manual save"
    finally:
        db.conn.close()
    from jebat.features.memory import EnhancedMemorySystem, MemoryType
    memory = EnhancedMemorySystem()
    memory.store("RECALL_BOUNDARY", memory_type=MemoryType.SEMANTIC, tags={"alpha", "beta"})
    recalled = command("repl", stdin="/recall RECALL_BOUNDARY\n/exit\n")
    assert "RECALL_BOUNDARY" in recalled.stdout and "Memory error:" not in recalled.stdout
    # Commit only in this disposable repository; quotes must remain literal data.
    for argv in (("init",), ("config", "user.name", "Workflow Check"), ("config", "user.email", "check@example.invalid")):
        subprocess.run(["git", *argv], check=True, capture_output=True)
    Path("proof.txt").write_text("isolated commit\n", encoding="utf-8")
    message = 'workflow "quoted" & literal message'
    command("repl", stdin=f"/commit {message}\n/exit\n")
    committed = subprocess.run(["git", "log", "-1", "--format=%s"], capture_output=True, text=True, check=True)
    assert committed.stdout.strip() == message
    print("PASS actual CLI resume/continue, missing-session errors, manual save")


def check_mcp():
    # Use the actual stdio entrypoint, not an in-process dispatch substitute.
    requests = [
        {"id": 1, "method": "initialize", "params": {"protocolVersion": "2026-07-28"}},
        {"id": 2, "method": "prompts/list", "params": {}},
        {"id": 3, "method": "resources/read", "params": {"uri": "jebat://workflow"}},
        {"id": 4, "method": "prompts/get", "params": {"name": "workflow-audit", "arguments": {"task": "Audit shell\nquoted \"scope\"", "scope": "."}}},
        {"id": 5, "method": "prompts/get", "params": {"name": "workflow-audit"}},
        {"id": 6, "method": "prompts/get", "params": {"name": "unknown"}},
        {"id": 7, "method": "prompts/get", "params": {"name": "workflow-audit", "arguments": {"task": 4}}},
        {"id": 8, "method": "prompts/get", "params": {"name": "project-onboard", "arguments": {"root": str(Path.cwd().parent)}}},
        {"id": 9, "method": "ping", "params": {}},
        {"id": 10, "method": "resources/read", "params": {"uri": "jebat://errors/recent"}},
    ]
    wire = "".join(json.dumps({"jsonrpc": "2.0", **req}) + "\n" for req in requests)
    result = command("mcp", "serve", "--transport", "stdio", stdin=wire)
    frames = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    responses = {frame["id"]: frame for frame in frames if "id" in frame}
    for ident in (5, 6, 7, 8):
        assert responses[ident]["error"]["code"] == -32602, responses[ident]
    assert "result" in responses[9], "Server died after invalid input"
    assert isinstance(json.loads(responses[10]["result"]["contents"][0]["text"]), list)
    from jebat.workflows import WORKFLOWS
    catalog = {item["name"]: item for item in responses[2]["result"]["prompts"]}
    assert set(WORKFLOWS) <= catalog.keys()
    for name in WORKFLOWS:
        assert any(arg["name"] == "scope" and not arg["required"] for arg in catalog[name]["arguments"])
        command("workflow", "show", name, "--task", "Review the requested path", "--scope", ".")
    cli_output = json.loads(command("workflow", "show", "workflow-audit", "--task", "-", "--scope", ".", "--json", stdin='Audit shell\nquoted "scope"').stdout)
    assert cli_output["text"] == responses[4]["result"]["messages"][0]["content"]["text"]
    assert command("workflow", "show", "workflow-audit", "--task", " ", ok=False).returncode == 2
    print("PASS real MCP handshake/catalog/errors/scope boundary; CLI/MCP playbook parity")


def check_http():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    environment = os.environ.copy()
    environment["JEBAT_API_KEY"] = "isolated-http-check"
    process = subprocess.Popen(
        [sys.executable, "-m", "jebat_cli_new", "mcp", "serve", "--transport", "http", "--port", str(port)],
        env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 15
        while True:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                assert process.poll() is None and time.monotonic() < deadline, "HTTP startup failed"
                time.sleep(0.1)
        url = f"http://127.0.0.1:{port}"
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}).encode()
        request = urllib.request.Request(url + "/message", data=body, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as exc:
            assert exc.code == 401
        else:
            raise AssertionError("Unauthenticated request accepted")
        request.add_header("X-API-Key", environment["JEBAT_API_KEY"])
        with urllib.request.urlopen(request, timeout=5) as response:
            assert response.status == 200 and json.load(response)["id"] == 1
        stream_request = urllib.request.Request(url + "/sse", headers={"X-API-Key": environment["JEBAT_API_KEY"]})
        with urllib.request.urlopen(stream_request, timeout=5) as stream:
            assert stream.status == 200
            assert stream.readline().decode().strip() == "event: endpoint"
            assert stream.readline().decode().strip() == "data: /message"
            stream.readline()
            init = urllib.request.Request(url + "/message", data=json.dumps({"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}).encode(), headers={"Content-Type": "application/json", "X-API-Key": environment["JEBAT_API_KEY"]})
            with urllib.request.urlopen(init, timeout=10) as response:
                assert "result" in json.load(response)
            assert stream.readline().decode().strip() == "event: message"
            notice = json.loads(stream.readline().decode().removeprefix("data: ").strip())
            assert notice["method"] == "notifications/advisorReady"
        print("PASS real HTTP auth denial/success, SSE endpoint and notification delivery")
    finally:
        process.terminate()
        process.communicate(timeout=10)


def worker():
    assert Path.home().resolve() == Path(os.environ["JEBAT_CHECK_HOME"]).resolve(), "Sandbox failed"
    asyncio.run(check_memory())
    asyncio.run(check_engine())
    check_dream()
    check_cli()
    check_mcp()
    check_http()
    print("PASS all isolated workflow checks; no live model, external delivery, or deployment")


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        worker()
    else:
        with tempfile.TemporaryDirectory(prefix="jebat-workflows-") as directory:
            home = Path(directory)
            workspace = home / "workflow-check-project"
            workspace.mkdir()
            environment = os.environ.copy()
            environment.update(
                HOME=str(home), USERPROFILE=str(home), JEBAT_CHECK_HOME=str(home),
                PYTHONUTF8="1", PYTHONPATH=str(ROOT), JEBAT_MCP_TERSE="1",
            )
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"], cwd=workspace, env=environment, timeout=240)
            raise SystemExit(result.returncode)
