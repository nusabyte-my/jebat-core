#!/usr/bin/env python3
"""JEBAT `design` subcommand — wrapper around the DESIGNmd CLI.

DESIGNmd (https://designmd.ai) is a registry of DESIGN.md design-system
specs. This module exposes it as `jebat design <subcommand>` so design
systems can be searched, fetched, downloaded (as a DESIGN.md), uploaded,
and tagged from inside the JEBAT CLI.

The wrapper shells out to the `designmd` npm binary. Install it once with:
    npm install -g designmd
and set DESIGNMD_API_KEY (export DESIGNMD_API_KEY=*** in your shell / .env).

Commands mirror the upstream CLI:
    jebat design search  "dark fintech" [--tag minimal] [--sort trending] [--limit N] [--json]
    jebat design get     <owner/name> [--json]
    jebat design download <owner/name> [-o ./DESIGN.md | --vault]
    jebat design upload  ./DESIGN.md --name "My Kit" --tags dark,saas
    jebat design tags
    jebat design sync    --tag dark --limit 5 [--vault]   # bulk pull into vault
    jebat design doctor                                # install/key/connectivity check
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

BINARY = os.environ.get("DESIGNMD_BIN", "designmd")
ENV_KEY = "DESIGNMD_API_KEY"

# Canonical vault location for downloaded design systems. Override with
# JEBAT_VAULT or pass --vault explicitly.
DEFAULT_VAULT = os.environ.get(
    "JEBAT_VAULT",
    os.path.join(os.path.dirname(__file__), "..", "..", "vault", "design-systems"),
)


def _which() -> str | None:
    return shutil.which(BINARY)


def _require() -> str:
    path = _which()
    if not path:
        sys.exit(
            "  designmd CLI not found. Install it with:\n"
            "    npm install -g designmd\n"
            "  and ensure it is on PATH (or set DESIGNMD_BIN)."
        )
    return path


def _ensure_key() -> bool:
    ok = bool(os.environ.get(ENV_KEY))
    if not ok:
        print(
            "  Note: DESIGNMD_API_KEY is not set. Search/get/tags work without it,\n"
            "  but upload requires `export DESIGNMD_API_KEY=***`.\n",
            file=sys.stderr,
        )
    return ok


def _run(args: list[str]) -> int:
    bin_ = _require()
    _ensure_key()
    try:
        return subprocess.call([bin_, *args])
    except FileNotFoundError:
        sys.exit(f"  designmd binary not executable: {bin_}")
    except KeyboardInterrupt:
        return 130


# ─── subcommand handlers ────────────────────────────────────────────

def cmd_search(args, _registry=None) -> int:
    cli = ["search", args.query]
    for t in (args.tag or []):
        cli += ["--tag", t]
    if args.sort:
        cli += ["--sort", args.sort]
    if args.limit:
        cli += ["--limit", str(args.limit)]
    if args.json:
        cli += ["--json"]
    return _run(cli)


def cmd_get(args, _registry=None) -> int:
    cli = ["get", args.name]
    if args.json:
        cli += ["--json"]
    return _run(cli)


def cmd_download(args, _registry=None) -> int:
    target = args.output
    if args.vault and not target:
        os.makedirs(DEFAULT_VAULT, exist_ok=True)
        safe = args.name.replace("/", "__")
        target = os.path.join(DEFAULT_VAULT, f"{safe}.md")
    cli = ["download", args.name]
    if target:
        cli += ["-o", target]
    rc = _run(cli)
    if rc == 0 and target:
        print(f"  saved -> {target}", file=sys.stderr)
    return rc


def cmd_upload(args, _registry=None) -> int:
    cli = ["upload", args.path, "--name", args.name]
    if args.tags:
        cli += ["--tags", args.tags]
    return _run(cli)


def cmd_tags(args, _registry=None) -> int:
    return _run(["tags"])


def cmd_sync(args, _registry=None) -> int:
    """Bulk-pull design systems matching a tag into the vault."""
    _require()
    _ensure_key()
    # Query upstream search (JSON) and pull each result's owner/name.
    cli = ["search", args.query or " ", "--limit", str(args.limit)]
    for t in (args.tag or []):
        cli += ["--tag", t]
    cli += ["--json"]
    try:
        out = subprocess.check_output([_which(), *cli], text=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"  designmd search failed (rc={e.returncode})\n{e.output}")
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        sys.exit("  designmd returned non-JSON (set DESIGNMD_API_KEY?); cannot sync.")
    results = data if isinstance(data, list) else data.get("results", [])
    if not results:
        print("  no matching design systems found.", file=sys.stderr)
        return 0
    vault = DEFAULT_VAULT
    if args.vault:
        vault = args.vault
    os.makedirs(vault, exist_ok=True)
    rc = 0
    for r in results:
        name = r.get("owner_name") or f"{r.get('owner','')}/{r.get('name','')}"
        if "/" not in name:
            continue
        safe = name.replace("/", "__")
        dest = os.path.join(vault, f"{safe}.md")
        print(f"  pulling {name} -> {dest}", file=sys.stderr)
        rc |= _run(["download", name, "-o", dest])
    return rc


def cmd_doctor(args, _registry=None) -> int:
    """Verify the integration is usable: binary, key, connectivity."""
    problems = 0
    bin_ = _which()
    if bin_:
        ver = subprocess.run([bin_, "--version"], capture_output=True, text=True)
        ver_str = (ver.stdout or "").strip() or "?"
        print(f"[ok] designmd binary: {bin_} ({ver_str})")
    else:
        problems += 1
        print("[FAIL] designmd binary not found on PATH. Run: npm install -g designmd")

    if os.environ.get(ENV_KEY):
        print(f"[ok] {ENV_KEY} is set")
    else:
        print(f"[warn] {ENV_KEY} not set — get/download/upload will fail. "
              f"Get one at https://designmd.ai/api-keys")

    if bin_:
        try:
            r = subprocess.run([bin_, "tags"], capture_output=True, text=True, timeout=30)
            if r.returncode == 0 and "tag" in r.stdout.lower():
                print("[ok] connectivity: reached designmd.ai (tags listed)")
            else:
                problems += 1
                print(f"[FAIL] connectivity: `designmd tags` rc={r.returncode}")
        except subprocess.TimeoutExpired:
            problems += 1
            print("[FAIL] connectivity: `designmd tags` timed out")
    print()
    print("doctor: " + ("OK" if problems == 0 else f"{problems} problem(s) found"))
    return 1 if problems else 0


# ─── argparse wiring (called from main.py) ──────────────────────────

def add_subparser(sub) -> None:
    p = sub.add_parser(
        "design",
        help="Search / download / upload DESIGN.md design systems (designmd.ai)",
    )
    dsub = p.add_subparsers(dest="action")

    s = dsub.add_parser("search", help="Search design systems")
    s.add_argument("query", help='e.g. "dark fintech"')
    s.add_argument("--tag", action="append", help="Filter by tag (repeatable)")
    s.add_argument("--sort", choices=["trending", "newest", "popular"])
    s.add_argument("--limit", type=int, help="Max results")
    s.add_argument("--json", action="store_true", help="JSON output")
    s.set_defaults(func=cmd_search)

    g = dsub.add_parser("get", help="View a design system")
    g.add_argument("name", help="owner/name, e.g. shafius/neon-fintech")
    g.add_argument("--json", action="store_true")
    g.set_defaults(func=cmd_get)

    d = dsub.add_parser("download", help="Download a design system as DESIGN.md")
    d.add_argument("name", help="owner/name")
    d.add_argument("-o", "--output", help="Output path (default: ./DESIGN.md)")
    d.add_argument("--vault", action="store_true",
                   help=f"Save into the vault ({os.path.normpath(DEFAULT_VAULT)})")
    d.set_defaults(func=cmd_download)

    u = dsub.add_parser("upload", help="Upload a DESIGN.md to your account")
    u.add_argument("path", help="Path to local DESIGN.md")
    u.add_argument("--name", required=True, help="Display name")
    u.add_argument("--tags", help="Comma-separated tags")
    u.set_defaults(func=cmd_upload)

    t = dsub.add_parser("tags", help="List available tags")
    t.set_defaults(func=cmd_tags)

    sy = dsub.add_parser("sync", help="Bulk-pull tag-matched systems into the vault")
    sy.add_argument("query", nargs="?", default=" ", help="Search query (default: space)")
    sy.add_argument("--tag", action="append", help="Filter by tag (repeatable)")
    sy.add_argument("--limit", type=int, default=5, help="Max results to pull")
    sy.add_argument("--vault", help="Override vault directory")
    sy.set_defaults(func=cmd_sync)

    doc = dsub.add_parser("doctor", help="Check install / key / connectivity")
    doc.set_defaults(func=cmd_doctor)


def dispatch(args, registry=None) -> int:
    if not getattr(args, "action", None):
        _run(["--help"])
        return 0
    handler = getattr(args, "func", None)
    if handler is None:
        _run(["--help"])
        return 0
    return handler(args, registry)
