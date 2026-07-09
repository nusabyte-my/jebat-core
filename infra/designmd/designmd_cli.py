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
    jebat design download <owner/name> [-o ./DESIGN.md]
    jebat design upload  ./DESIGN.md --name "My Kit" --tags dark,saas
    jebat design tags
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

BINARY = os.environ.get("DESIGNMD_BIN", "designmd")
ENV_KEY = "DESIGNMD_API_KEY"


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


def _ensure_key() -> None:
    if not os.environ.get(ENV_KEY):
        # Don't hard-fail — designmd itself will error with a clearer message.
        # We surface a hint so users know why an upload/search might 401.
        print(
            "  Note: DESIGNMD_API_KEY is not set. Search/get/tags work without it,\n"
            "  but upload requires `export DESIGNMD_API_KEY=***`.\n",
            file=sys.stderr,
        )


def _run(args: list[str]) -> int:
    bin_ = _require()
    _ensure_key()
    try:
        # Inherit stdout/stderr so the upstream CLI's formatting + colors pass through.
        return subprocess.call([bin_, *args])
    except FileNotFoundError:
        sys.exit(f"  designmd binary not executable: {bin_}")
    except KeyboardInterrupt:
        return 130


# ─── subcommand handlers ────────────────────────────────────────────

def cmd_search(args, _registry=None) -> int:
    cli = ["search", args.query]
    if args.tag:
        for t in args.tag:
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
    cli = ["download", args.name]
    if args.output:
        cli += ["-o", args.output]
    return _run(cli)


def cmd_upload(args, _registry=None) -> int:
    cli = ["upload", args.path, "--name", args.name]
    if args.tags:
        cli += ["--tags", args.tags]
    return _run(cli)


def cmd_tags(args, _registry=None) -> int:
    return _run(["tags"])


# ─── argparse wiring (called from main.py) ──────────────────────────

def add_subparser(sub) -> None:
    """Register the `design` subcommand on the JEBAT argparse subparsers."""
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
    d.set_defaults(func=cmd_download)

    u = dsub.add_parser("upload", help="Upload a DESIGN.md to your account")
    u.add_argument("path", help="Path to local DESIGN.md")
    u.add_argument("--name", required=True, help="Display name")
    u.add_argument("--tags", help="Comma-separated tags")
    u.set_defaults(func=cmd_upload)

    t = dsub.add_parser("tags", help="List available tags")
    t.set_defaults(func=cmd_tags)


def dispatch(args, registry=None) -> int:
    """Entry point used by main.main() for `jebat design ...`."""
    if not getattr(args, "action", None):
        # No sub-action: show help.
        _run(["--help"])
        return 0
    handler = getattr(args, "func", None)
    if handler is None:
        _run(["--help"])
        return 0
    return handler(args, registry)
