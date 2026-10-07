"""Run: python scripts/check_webui_auth.py. Real launcher, temporary credentials, no model calls."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def probe(base: str, path: str, key: str | None = None):
    request = urllib.request.Request(base + path, headers={"X-API-Key": key} if key else {})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def main():
    with tempfile.TemporaryDirectory(prefix="jebat-webui-auth-") as directory:
        home = Path(directory)
        workspace = home / "workspace"
        workspace.mkdir()
        (home / ".jebat").mkdir()
        # A provider-only secrets file must not hide API auth in workspace .env.
        (home / ".jebat" / "secrets.env").write_text("OPENAI_API_KEY=isolated-provider-fixture\n", encoding="utf-8")
        (workspace / ".env").write_text("JEBAT_ENV=production\nJEBAT_API_KEY=isolated-webui-fixture\n", encoding="utf-8")
        environment = os.environ.copy()
        for name in ("JEBAT_API_KEY", "JEBAT_ENV", "JEBAT_API_KEY_ALLOW_QUERY"):
            environment.pop(name, None)
        environment.update(HOME=str(home), USERPROFILE=str(home), PYTHONPATH=str(ROOT), PYTHONUTF8="1",
                           JEBAT_WEBUI_WARMUP="0", JEBAT_WIKI_DIR=str(home / "wiki"))
        # Explicit process environment retains precedence over both files.
        explicit = dict(environment, JEBAT_API_KEY="process-wins")
        check = subprocess.run([sys.executable, "-c",
            "import os; from jebat.llm.auth import _ensure_secrets_loaded; _ensure_secrets_loaded(); "
            "assert os.environ['JEBAT_API_KEY']=='process-wins'; assert os.environ['JEBAT_ENV']=='production'"],
            cwd=workspace, env=explicit, capture_output=True, text=True, timeout=30)
        assert check.returncode == 0, check.stderr
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        process = subprocess.Popen([sys.executable, "-m", "jebat.services.webui.launch", "--host", "127.0.0.1", "--port", str(port)],
                                   cwd=workspace, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        base = f"http://127.0.0.1:{port}"
        try:
            deadline = time.monotonic() + 25
            while True:
                try:
                    if probe(base, "/health")[0] == 200:
                        break
                except OSError:
                    pass
                if process.poll() is not None or time.monotonic() > deadline:
                    raise AssertionError("WebUI failed to become ready")
                time.sleep(0.1)
            assert probe(base, "/webui/")[0] == 200
            for path in ("/webui/api/status", "/api/system/metrics", "/api/keris/history"):
                assert probe(base, path)[0] == 401, path
                assert probe(base, path, "wrong-key")[0] == 403, path
                status, body = probe(base, path, "isolated-webui-fixture")
                payload = json.loads(body)
                if path.endswith('metrics') and status == 503:
                    assert payload['error'] == 'metrics_unavailable'
                    assert 'cpu_percent' not in payload
                else:
                    assert status == 200, (path, status)
                    if path.endswith('metrics'):
                        assert 'cpu_percent' in payload and 'uptime_seconds' in payload
                    elif path.endswith('status'):
                        assert payload['status'] and 'components' in payload
            assert probe(base, "/webui/api/status?api_key=isolated-webui-fixture")[0] == 401
            print("PASS real WebUI: public shell, protected reads 401/403/200, query-key rejection, environment precedence")
        finally:
            process.terminate()
            process.communicate(timeout=15)
        # Missing production key must fail closed, not start an open API.
        (workspace / ".env").write_text("JEBAT_ENV=production\n", encoding="utf-8")
        check = subprocess.run([sys.executable, "-c",
            "from jebat.llm.auth import _ensure_secrets_loaded; _ensure_secrets_loaded(); "
            "from jebat.api.auth import APIKeyMiddleware; APIKeyMiddleware(object())"],
            cwd=workspace, env=environment, capture_output=True, text=True, timeout=30)
        assert check.returncode != 0 and "JEBAT_API_KEY must be set" in check.stderr
        print("PASS production without API key fails closed; no production credentials or state used")


if __name__ == "__main__":
    main()
