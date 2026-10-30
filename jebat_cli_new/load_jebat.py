"""JEBAT startup loading, release checks, and update guidance."""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from pathlib import Path
from typing import Any, Dict, Optional

from jebat_cli_new import __version__

RELEASE_URL = "https://api.github.com/repos/nusabyte-my/jebat-core/releases/latest"
CACHE_TTL = 3600


def cache_path() -> Path:
    return Path.home() / ".jebat" / "latest-release.json"


def fetch_latest_release(timeout: float = 3.0) -> Optional[Dict[str, Any]]:
    request = urllib.request.Request(RELEASE_URL, headers={"Accept": "application/vnd.github+json", "User-Agent": "JEBAT-CLI"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response.sock.settimeout(timeout) if getattr(response, "sock", None) else None
        data = json.loads(response.read().decode("utf-8"))
    return {
        "version": str(data.get("tag_name", "")).lstrip("v"),
        "name": data.get("name") or data.get("tag_name"),
        "url": data.get("html_url"),
        "published_at": data.get("published_at"),
        "body": data.get("body") or "",
        "checked_at": time.time(),
    }


def latest_release(*, allow_network: bool = True) -> Optional[Dict[str, Any]]:
    path = cache_path()
    cached = None
    if path.is_file():
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            cached = None
    if cached and time.time() - cached.get("checked_at", 0) < CACHE_TTL:
        return cached
    if not allow_network:
        return cached
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            release = pool.submit(fetch_latest_release).result(timeout=3.0)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(release, indent=2), encoding="utf-8")
        return release
    except Exception:
        return cached


def update_summary(current: str = __version__, release: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    current_parts = tuple(int(part) for part in current.split(".") if part.isdigit())
    latest = release.get("version") if release else None
    latest_parts = tuple(int(part) for part in latest.split(".") if part.isdigit()) if latest else None
    return {
        "current": current,
        "latest": latest,
        "update_available": bool(latest_parts and latest_parts > current_parts),
        "release": release,
    }


def load_jebat(*, check_latest: bool = False, interactive: bool = False) -> Dict[str, Any]:
    """Load startup context and report the latest release without forcing updates."""
    summary = update_summary(__version__, latest_release(allow_network=check_latest) if check_latest else None)
    print(f"JEBAT {summary['current']} loaded")
    if summary["latest"]:
        release = summary["release"]
        print(f"Latest: {release.get('name')} ({summary['latest']})")
        if release.get("url"):
            print(f"Release: {release['url']}")
        if summary["update_available"]:
            print(f"Update available: {summary['current']} → {summary['latest']}")
            print("Update: python -m pip install -e .")
            if interactive and sys.stdin.isatty() and sys.stdout.isatty():
                answer = input("Update now? [y/N] ").strip().lower()
                if answer in {"y", "yes"}:
                    result = subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=False)
                    summary["update_exit_code"] = result.returncode
        else:
            print("You are on the latest release.")
    else:
        print("Latest release information unavailable (offline or API unavailable).")
    return summary


def main() -> int:
    load_jebat()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
