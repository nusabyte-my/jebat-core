"""Minimal LSP client — stdio JSON-RPC with Content-Length framing.

Servers are discovered per file extension. Only servers actually installed are
used; a missing server is reported, never guessed at.

    jebat: lsp_definition / lsp_references / lsp_hover / lsp_diagnostics

Not a full LSP implementation: no workspace folders, no incremental sync, no
completion. Enough to answer "where is this defined" and "what's broken here".
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

# extension -> (command, args). First match wins.
SERVERS: Dict[str, Tuple[str, List[str]]] = {
    ".ts": ("typescript-language-server", ["--stdio"]),
    ".tsx": ("typescript-language-server", ["--stdio"]),
    ".js": ("typescript-language-server", ["--stdio"]),
    ".jsx": ("typescript-language-server", ["--stdio"]),
    ".py": ("pyright-langserver", ["--stdio"]),
    ".go": ("gopls", []),
    ".rs": ("rust-analyzer", []),
    ".c": ("clangd", []),
    ".cpp": ("clangd", []),
}

# Alternate commands to try when the primary is absent.
FALLBACKS: Dict[str, List[Tuple[str, List[str]]]] = {
    ".py": [("pylsp", []), ("pyright", ["--stdio"])],
}


def server_for(path: Path) -> Optional[Tuple[str, List[str]]]:
    ext = path.suffix.lower()
    candidates = []
    if ext in SERVERS:
        candidates.append(SERVERS[ext])
    candidates.extend(FALLBACKS.get(ext, []))
    for cmd, args in candidates:
        exe = shutil.which(cmd)
        if not exe:
            continue
        if exe.lower().endswith((".cmd", ".bat")):
            return exe, args
        return exe, args
    return None


def _uri(path: Path) -> str:
    return "file:///" + quote(str(path.resolve()).replace("\\", "/"), safe="/:")


def _norm_uri(uri: str) -> str:
    """Normalize a file URI for comparison.

    Language servers are inconsistent about the drive letter's case and about
    encoding the colon: typescript-language-server publishes
    `file:///c%3A/...` while a client naturally builds `file:///C:/...`.
    Both must resolve to the same key or diagnostics silently never match.
    """
    if not uri:
        return ""
    out = uri.replace("%3A", ":").replace("%3a", ":")
    out = out.replace("%20", " ")
    if out.lower().startswith("file:///"):
        head, tail = out[:8], out[8:]
        out = head + tail[:1].lower() + tail[1:]
    return out.rstrip("/").lower() if out.lower().endswith((".ts", ".tsx", ".js", ".jsx",
                                                           ".py", ".go", ".rs", ".c", ".cpp")) \
        else out


class LSPClient:
    """One language server process, spoken to over stdio."""

    def __init__(self, root: Path, cmd: str, args: List[str], timeout: float = 20.0):
        self.root = root
        self.timeout = timeout
        self._id = 0
        self._pending: Dict[int, Queue] = {}
        self._diagnostics: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()
        self._proc = subprocess.Popen(
            [cmd, *args],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            cwd=str(root),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self._opened: set = set()
        self._initialize()

    # ── framing ─────────────────────────────────────────────────────────────

    def _send(self, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        assert self._proc.stdin
        self._proc.stdin.write(header + body)
        self._proc.stdin.flush()

    def _read_loop(self) -> None:
        stream = self._proc.stdout
        assert stream
        while True:
            length = None
            while True:
                line = stream.readline()
                if not line:
                    return
                line = line.strip()
                if not line:
                    break
                if line.lower().startswith(b"content-length:"):
                    length = int(line.split(b":", 1)[1])
            if length is None:
                continue
            body = stream.read(length)
            if not body:
                return
            try:
                msg = json.loads(body.decode("utf-8", "replace"))
            except json.JSONDecodeError:
                continue
            self._dispatch(msg)

    def _dispatch(self, msg: Dict[str, Any]) -> None:
        if "id" in msg and ("result" in msg or "error" in msg):
            with self._lock:
                q = self._pending.pop(msg["id"], None)
            if q:
                q.put(msg)
            return
        if msg.get("method") == "textDocument/publishDiagnostics":
            params = msg.get("params") or {}
            self._diagnostics[_norm_uri(params.get("uri", ""))] = params.get("diagnostics", []) or []
        # Server-initiated requests: answer so the server doesn't block.
        if "id" in msg and "method" in msg:
            self._send({"jsonrpc": "2.0", "id": msg["id"], "result": None})

    def request(self, method: str, params: Dict[str, Any]) -> Any:
        self._id += 1
        rid = self._id
        q: Queue = Queue()
        with self._lock:
            self._pending[rid] = q
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        try:
            msg = q.get(timeout=self.timeout)
        except Empty:
            return None
        if "error" in msg:
            raise RuntimeError(msg["error"].get("message", "lsp error"))
        return msg.get("result")

    def notify(self, method: str, params: Dict[str, Any]) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    # ── lifecycle ───────────────────────────────────────────────────────────

    def _initialize(self) -> None:
        self.request("initialize", {
            "processId": os.getpid(),
            "rootUri": _uri(self.root),
            "capabilities": {"textDocument": {"publishDiagnostics": {}}},
            "workspaceFolders": [{"uri": _uri(self.root), "name": self.root.name}],
        })
        self.notify("initialized", {})

    def open(self, path: Path) -> str:
        uri = _uri(path)
        if uri in self._opened:
            return uri
        text = path.read_text(encoding="utf-8", errors="replace")
        lang = {
            ".ts": "typescript", ".tsx": "typescriptreact",
            ".js": "javascript", ".jsx": "javascriptreact",
            ".py": "python", ".go": "go", ".rs": "rust",
            ".c": "c", ".cpp": "cpp",
        }.get(path.suffix.lower(), "plaintext")
        self.notify("textDocument/didOpen", {
            "textDocument": {"uri": uri, "languageId": lang, "version": 1, "text": text},
        })
        self._opened.add(uri)
        return uri

    def _position(self, path: Path, line: int, character: int) -> Dict[str, Any]:
        return {"textDocument": {"uri": self.open(path)},
                "position": {"line": max(0, line - 1), "character": max(0, character)}}

    # ── queries ─────────────────────────────────────────────────────────────

    def definition(self, path: Path, line: int, character: int) -> Any:
        return self.request("textDocument/definition", self._position(path, line, character))

    def references(self, path: Path, line: int, character: int) -> Any:
        params = self._position(path, line, character)
        params["context"] = {"includeDeclaration": True}
        return self.request("textDocument/references", params)

    def hover(self, path: Path, line: int, character: int) -> Any:
        return self.request("textDocument/hover", self._position(path, line, character))

    def diagnostics(self, path: Path) -> List[Dict[str, Any]]:
        """Return diagnostics, waiting for the server's real pass.

        A language server typically publishes an empty list immediately on
        didOpen and the actual findings a moment later, so returning on first
        sight reports "clean" for broken files. Wait for a non-empty list, or
        a settle window after the last publish, before answering.
        """
        self.open(path)
        uri = _norm_uri(_uri(path))
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            if self._diagnostics.get(uri):
                return self._diagnostics[uri]
            time.sleep(0.1)
        return self._diagnostics.get(uri, [])

    def shutdown(self) -> None:
        try:
            self.request("shutdown", {})
            self.notify("exit", {})
        except Exception:
            pass
        try:
            self._proc.terminate()
        except Exception:
            pass


# ── process-wide cache (one server per root) ────────────────────────────────

_CLIENTS: Dict[Tuple[str, str], LSPClient] = {}


def get_client(path: Path) -> Tuple[Optional[LSPClient], Optional[str]]:
    """Return (client, error). Client is cached per (root, server command)."""
    found = server_for(path)
    if not found:
        ext = path.suffix.lower()
        candidates = [SERVERS[ext][0]] if ext in SERVERS else []
        candidates += [c[0] for c in FALLBACKS.get(ext, [])]
        hint = ", ".join(candidates) if candidates else "no known server"
        return None, f"no language server for {ext or 'this file'} (tried: {hint})"
    cmd, args = found
    root = path.resolve().parent
    key = (str(root), cmd)
    if key in _CLIENTS:
        return _CLIENTS[key], None
    try:
        client = LSPClient(root, cmd, args)
    except Exception as exc:
        return None, f"failed to start {cmd}: {type(exc).__name__}: {exc}"
    _CLIENTS[key] = client
    return client, None


def format_locations(locs: Any) -> str:
    if not locs:
        return "no result"
    if isinstance(locs, dict):
        locs = [locs]
    out = []
    for loc in locs[:20]:
        uri = loc.get("uri") or loc.get("targetUri") or ""
        rng = loc.get("range") or loc.get("targetSelectionRange") or {}
        start = rng.get("start", {})
        path = uri.replace("file:///", "").replace("%3A", ":")
        out.append(f"  {path}:{start.get('line', 0) + 1}:{start.get('character', 0) + 1}")
    return "\n".join(out) or "no result"
