"""
DESIGN.md Integration — Design System Search & Download

Wraps the designmd CLI (npm @google/design.md) for searching,
downloading, and managing DESIGN.md files from designmd.ai.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DesignSystem:
    """A design system from designmd.ai."""
    slug: str
    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    author: str = ""
    downloads: int = 0
    likes: int = 0
    content: str = ""


class DesignMDClient:
    """Client for the designmd CLI."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def _run(self, args: list[str], timeout: int = 30) -> dict[str, Any]:
        """Run a designmd CLI command."""
        cmd = ["npx", "-y", "designmd"] + args
        env = {}
        if self.api_key:
            env["DESIGNMD_API_KEY"] = self.api_key

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**dict(__import__("os").environ), **env},
            )
            if result.returncode == 0:
                # Try JSON parse first
                try:
                    return {"ok": True, "data": json.loads(result.stdout)}
                except json.JSONDecodeError:
                    return {"ok": True, "text": result.stdout}
            else:
                return {"ok": False, "error": result.stderr.strip() or result.stdout.strip()}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Command timed out"}
        except FileNotFoundError:
            return {"ok": False, "error": "designmd CLI not found. Install: npm install -g designmd"}

    def search(
        self,
        query: str,
        tags: list[str] | None = None,
        sort: str = "trending",
        limit: int = 5,
    ) -> tuple[list[DesignSystem], str]:
        """Search for design systems."""
        args = ["search", query, "--sort", sort, "--limit", str(limit), "--json"]
        if tags:
            for tag in tags:
                args.extend(["--tag", tag])

        result = self._run(args)
        if not result["ok"]:
            return [], result.get("error", "Search failed")

        data = result.get("data", [])
        systems = []
        for item in data:
            systems.append(DesignSystem(
                slug=item.get("slug", ""),
                name=item.get("name", ""),
                description=item.get("description", ""),
                tags=item.get("tags", []),
                author=item.get("author", ""),
                downloads=item.get("downloads", 0),
                likes=item.get("likes", 0),
            ))
        return systems, ""

    def get(self, slug: str) -> tuple[DesignSystem | None, str]:
        """Get a design system's details and content."""
        result = self._run(["get", slug, "--json"])
        if not result["ok"]:
            return None, result.get("error", "Get failed")

        data = result.get("data", {})
        system = DesignSystem(
            slug=data.get("slug", slug),
            name=data.get("name", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            author=data.get("author", ""),
            downloads=data.get("downloads", 0),
            likes=data.get("likes", 0),
            content=data.get("content", ""),
        )
        return system, ""

    def download(
        self,
        slug: str,
        output_path: str | Path | None = None,
    ) -> tuple[bool, str]:
        """Download a design system as DESIGN.md."""
        args = ["download", slug]
        if output_path:
            args.extend(["-o", str(output_path)])

        result = self._run(args, timeout=60)
        if result["ok"]:
            text = result.get("text", "")
            return True, text.strip() if text else f"Downloaded {slug}"
        return False, result.get("error", "Download failed")

    def upload(
        self,
        file_path: str | Path,
        name: str | None = None,
        tags: list[str] | None = None,
    ) -> tuple[bool, str]:
        """Upload a DESIGN.md file."""
        args = ["upload", str(file_path)]
        if name:
            args.extend(["--name", name])
        if tags:
            args.extend(["--tags", ",".join(tags)])

        result = self._run(args, timeout=60)
        if result["ok"]:
            return True, result.get("text", "Uploaded successfully")
        return False, result.get("error", "Upload failed")

    def lint(self, file_path: str | Path) -> tuple[bool, str]:
        """Lint a DESIGN.md file."""
        result = self._run(["lint", str(file_path)])
        if result["ok"]:
            return True, result.get("text", "Lint passed")
        return False, result.get("error", "Lint failed")

    def export_tailwind(self, file_path: str | Path) -> tuple[bool, str]:
        """Export DESIGN.md to Tailwind theme JSON."""
        result = self._run(["export", "--format", "tailwind", str(file_path)])
        if result["ok"]:
            return True, result.get("text", "")
        return False, result.get("error", "Export failed")

    def export_dtcg(self, file_path: str | Path) -> tuple[bool, str]:
        """Export DESIGN.md to W3C DTCG JSON."""
        result = self._run(["export", "--format", "dtcg", str(file_path)])
        if result["ok"]:
            return True, result.get("text", "")
        return False, result.get("error", "Export failed")

    def tags(self) -> tuple[list[str], str]:
        """List available tags."""
        result = self._run(["tags"])
        if result["ok"]:
            text = result.get("text", "")
            tags_list = [t.strip() for t in text.splitlines() if t.strip()]
            return tags_list, ""
        return [], result.get("error", "Failed to list tags")
