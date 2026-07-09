#!/usr/bin/env python3
"""Integration tests for the Jebat unified inference stack.

Hits the LIVE stack (router :8000, openwebui :8080) and asserts behavior.
Stdlib only (urllib) so it runs in any venv without pytest.

Run:  python test_infer_stack.py
Exit 0 = all pass.
"""
import json
import sys
import urllib.request
import urllib.error

ROUTER = "http://127.0.0.1:8000"
OWUI = "http://127.0.0.1:8080"

passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def post(path, payload, timeout=30):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        ROUTER + path, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get(path, timeout=10):
    req = urllib.request.Request(ROUTER + path)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


print("== 1. Router health ==")
try:
    h = get("/health")
    check("router up", h.get("router") == "up", h)
    check("llamacpp backend up", h["backends"].get("llamacpp") == "up", h)
    check("ollama backend up", h["backends"].get("ollama") == "up", h)
    check("remote_ollama present (graceful)", "remote_ollama" in h["backends"], h)
except Exception as e:
    check("router reachable", False, repr(e))

print("== 2. Merged models list ==")
try:
    m = get("/v1/models")
    ids = [x["id"] for x in m.get("data", [])]
    check("qwen2.5:3b listed", "qwen2.5:3b" in ids, ids)
    check("qwen2.5-3b-cpp alias listed", "qwen2.5-3b-cpp" in ids, ids)
    check("nomic-embed-text listed", any("nomic-embed" in i for i in ids), ids)
except Exception as e:
    check("models listed", False, repr(e))

print("== 3. Chat via Ollama (default route) ==")
try:
    r = post("/v1/chat/completions", {
        "model": "qwen2.5:3b",
        "messages": [{"role": "user", "content": "Reply with exactly: T_OK"}],
        "max_tokens": 8,
    })
    content = r["choices"][0]["message"]["content"]
    check("ollama chat returns text", len(content) > 0, content)
    check("ollama model echoed", r.get("model") == "qwen2.5:3b", r.get("model"))
except Exception as e:
    check("ollama chat", False, repr(e))

print("== 4. Chat via llama.cpp (alias route) ==")
try:
    r = post("/v1/chat/completions", {
        "model": "qwen2.5-3b-cpp",
        "messages": [{"role": "user", "content": "Reply with exactly: CPP_OK"}],
        "max_tokens": 8,
    })
    content = r["choices"][0]["message"]["content"]
    check("llamacpp chat returns text", len(content) > 0, content)
except Exception as e:
    check("llamacpp chat", False, repr(e))

print("== 5. Forced backend suffix routing ==")
try:
    r = post("/v1/chat/completions", {
        "model": "qwen2.5:3b@ollama",
        "messages": [{"role": "user", "content": "Reply with exactly: FORCE_OK"}],
        "max_tokens": 8,
    })
    content = r["choices"][0]["message"]["content"]
    check("suffix @ollama routes", len(content) > 0, content)
except Exception as e:
    check("suffix @ollama routing", False, repr(e))

print("== 6. Embeddings ==")
try:
    r = post("/v1/embeddings", {"model": "nomic-embed-text", "input": "hello world"}, timeout=30)
    vec = r.get("data", [{}])[0].get("embedding", [])
    check("embedding vector returned", len(vec) > 0, f"len={len(vec)}")
    check("embedding dim sane", len(vec) in (384, 768, 1024, 1536, 2048), f"dim={len(vec)}")
except Exception as e:
    check("embeddings", False, repr(e))

print("== 7. Remote backend graceful failure ==")
try:
    h = get("/health")
    remote = h["backends"].get("remote_ollama", "")
    # either reachable (up) or gracefully down — never crash the router
    check("remote_ollama does not break router",
          remote.startswith("up") or "down" in remote, remote)
    # if reachable, actually route to it
    if remote.startswith("up"):
        r = post("/v1/chat/completions", {
            "model": "qwen2.5:14b@remote_ollama",
            "messages": [{"role": "user", "content": "hi"}], "max_tokens": 8,
        })
        check("remote chat works when up", "choices" in r, r)
except Exception as e:
    check("remote graceful", False, repr(e))

print("== 8. OpenWebUI health ==")
try:
    req = urllib.request.Request(OWUI + "/health")
    with urllib.request.urlopen(req, timeout=10) as r:
        body = json.loads(r.read().decode())
    check("openwebui healthy", body.get("status") is True, body)
except Exception as e:
    check("openwebui health", False, repr(e))

print(f"\nRESULT: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
