"""VS Code workspace capture support for JEBAT projects."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "jebat.workspace.capture.v1"


PROJECT_TYPE_INDICATORS: dict[str, list[str]] = {
    "nextjs": ["next.config.js", "next.config.mjs", "app", "pages"],
    "react": ["package.json", "src/App.jsx", "src/App.tsx"],
    "vue": ["package.json", "src/App.vue", "vite.config.js"],
    "angular": ["angular.json", "src/app/app.component.ts"],
    "node": ["package.json", "server.js", "index.js", "src/index.js"],
    "typescript": ["tsconfig.json"],
    "python": ["pyproject.toml", "requirements.txt", "main.py", "app.py"],
    "django": ["manage.py"],
    "flask": ["app.py", "wsgi.py"],
    "go": ["go.mod"],
    "rust": ["Cargo.toml"],
}


STACK_FILES: dict[str, list[str]] = {
    "node": ["package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json"],
    "python": ["pyproject.toml", "requirements.txt", "Pipfile", "poetry.lock", "uv.lock"],
    "go": ["go.mod"],
    "rust": ["Cargo.toml"],
    "docker": ["Dockerfile", "docker-compose.yml", "compose.yml"],
    "database": ["prisma/schema.prisma", "drizzle.config.ts", "alembic.ini"],
}


KEY_DIRECTORIES = [
    "src",
    "app",
    "pages",
    "components",
    "lib",
    "server",
    "api",
    "tests",
    "test",
    "docs",
    "scripts",
    "database",
    "migrations",
]


ENTRYPOINT_FILES = [
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "main.py",
    "app.py",
    "server.js",
    "index.js",
    "src/main.ts",
    "src/index.ts",
    "src/main.tsx",
    "src/App.tsx",
    "go.mod",
    "Cargo.toml",
    "Dockerfile",
    "docker-compose.yml",
    "compose.yml",
]


@dataclass(frozen=True)
class CaptureResult:
    """Files written by a workspace capture run."""

    snapshot: dict[str, Any]
    written: list[Path]
    skipped: list[Path]


class WorkspaceCapture:
    """Capture project startup context into repo-local VS Code files."""

    def __init__(self, project_root: Path):
        self.project_root = project_root.expanduser().resolve()
        if not self.project_root.exists():
            raise FileNotFoundError(f"Project path not found: {self.project_root}")
        if not self.project_root.is_dir():
            raise NotADirectoryError(f"Project path is not a directory: {self.project_root}")

    def build_snapshot(self) -> dict[str, Any]:
        """Build a deterministic project snapshot from local files."""
        project_type = self._detect_project_type()
        stack = self._detect_stack()
        commands = self._detect_commands()
        directories = self._detect_directories()
        entrypoints = self._detect_entrypoints()

        return {
            "schema": SCHEMA_VERSION,
            "capturedAt": datetime.now(timezone.utc).isoformat(),
            "project": {
                "name": self.project_root.name,
                "root": str(self.project_root),
                "type": project_type,
                "stack": stack,
            },
            "assistant": {
                "mode": "Panglima",
                "captureFirst": True,
                "defaultSkills": self._suggest_skills(project_type, stack),
                "firstResponse": [
                    "project snapshot",
                    "active skills",
                    "first plan",
                    "risks or blockers",
                ],
            },
            "entrypoints": entrypoints,
            "directories": directories,
            "commands": commands,
            "constraints": [
                "Confirm the real project objective before implementation.",
                "Read local AGENTS.md, MEMORY.md, and DESIGN.md when present.",
                "Do not commit secrets or edit environment files with real credentials.",
                "Prefer the smallest verified change for the requested outcome.",
            ],
            "risks": self._detect_risks(commands, entrypoints),
            "nextActions": [
                "Open this project root as the VS Code workspace folder.",
                "Review PROJECT_START.md before the first implementation task.",
                "Use the generated Copilot instructions to keep chat capture-first.",
            ],
        }

    def write_vscode_capture(
        self,
        *,
        overwrite: bool = False,
        include_copilot: bool = True,
    ) -> CaptureResult:
        """Write VS Code capture artifacts into the target project."""
        snapshot = self.build_snapshot()
        files = {
            self.project_root / ".vscode" / "jebat-workspace.json": self._json(snapshot),
            self.project_root / "PROJECT_START.md": self._project_start(snapshot),
        }
        if include_copilot:
            files[self.project_root / ".github" / "copilot-instructions.md"] = (
                self._copilot_instructions(snapshot)
            )

        written: list[Path] = []
        skipped: list[Path] = []
        for path, content in files.items():
            if path.exists() and not overwrite:
                skipped.append(path)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            written.append(path)

        return CaptureResult(snapshot=snapshot, written=written, skipped=skipped)

    def _detect_project_type(self) -> str:
        scores: list[tuple[str, int]] = []
        for project_type, indicators in PROJECT_TYPE_INDICATORS.items():
            matches = sum(1 for item in indicators if (self.project_root / item).exists())
            if matches:
                scores.append((project_type, matches))
        if not scores:
            return "generic"
        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[0][0]

    def _detect_stack(self) -> list[str]:
        stack = []
        for name, files in STACK_FILES.items():
            if any((self.project_root / item).exists() for item in files):
                stack.append(name)
        return stack or ["generic"]

    def _detect_directories(self) -> list[str]:
        return [item for item in KEY_DIRECTORIES if (self.project_root / item).is_dir()]

    def _detect_entrypoints(self) -> list[str]:
        return [item for item in ENTRYPOINT_FILES if (self.project_root / item).exists()]

    def _detect_commands(self) -> dict[str, str]:
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                package = json.loads(package_json.read_text(encoding="utf-8"))
                scripts = package.get("scripts", {})
            except json.JSONDecodeError:
                scripts = {}
            commands: dict[str, str] = {}
            package_manager = self._detect_package_manager()
            for name in ["dev", "start", "test", "build", "lint"]:
                if name in scripts:
                    commands[name] = f"{package_manager} run {name}"
            if commands:
                commands["install"] = f"{package_manager} install"
                return commands

        if (self.project_root / "pyproject.toml").exists():
            return {"install": "python -m pip install -e .", "test": "pytest"}
        if (self.project_root / "requirements.txt").exists():
            return {"install": "python -m pip install -r requirements.txt", "test": "pytest"}
        if (self.project_root / "go.mod").exists():
            return {"test": "go test ./...", "build": "go build ./..."}
        if (self.project_root / "Cargo.toml").exists():
            return {"test": "cargo test", "build": "cargo build"}
        return {}

    def _detect_package_manager(self) -> str:
        if (self.project_root / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (self.project_root / "yarn.lock").exists():
            return "yarn"
        return "npm"

    def _suggest_skills(self, project_type: str, stack: list[str]) -> list[str]:
        skills = ["panglima"]
        if "python" in stack:
            skills.append("python-patterns")
        if "node" in stack or project_type in {"react", "nextjs", "vue", "angular"}:
            skills.append("typescript-expert")
        if project_type in {"react", "nextjs", "vue", "angular"}:
            skills.append("react-patterns")
        if "docker" in stack:
            skills.append("docker-expert")
        return skills[:3]

    def _detect_risks(self, commands: dict[str, str], entrypoints: list[str]) -> list[str]:
        risks = []
        if not commands:
            risks.append("No obvious run, build, or test commands were detected.")
        if not entrypoints:
            risks.append("No common entrypoint files were detected.")
        if (self.project_root / ".env").exists():
            risks.append("A .env file exists; keep credentials out of generated context.")
        return risks or ["No immediate structural risks detected from file names alone."]

    def _json(self, snapshot: dict[str, Any]) -> str:
        return json.dumps(snapshot, indent=2) + "\n"

    def _project_start(self, snapshot: dict[str, Any]) -> str:
        project = snapshot["project"]
        commands = snapshot["commands"]
        risks = snapshot["risks"]
        skills = ", ".join(snapshot["assistant"]["defaultSkills"])

        command_lines = "\n".join(
            f"- {name}: `{command}`" for name, command in commands.items()
        ) or "- Not detected yet."
        risk_lines = "\n".join(f"- {risk}" for risk in risks)
        entrypoints = ", ".join(snapshot["entrypoints"]) or "Not detected yet."
        directories = ", ".join(snapshot["directories"]) or "Not detected yet."

        return f"""# Project Start

## Capture

- Project: {project["name"]}
- Type: {project["type"]}
- Stack: {", ".join(project["stack"])}
- Default assistant mode: Panglima
- Suggested skills: {skills}

## Entrypoints

{entrypoints}

## Key Directories

{directories}

## Commands

{command_lines}

## Risks

{risk_lines}

## Operating Rule

Before implementation, capture the objective, constraints, success criteria, and verification path.
"""

    def _copilot_instructions(self, snapshot: dict[str, Any]) -> str:
        project = snapshot["project"]
        skills = ", ".join(snapshot["assistant"]["defaultSkills"])

        return f"""# JEBAT Project Instructions

You are JEBAT operating in Panglima capture-first mode for this VS Code workspace.

## Project

- Name: {project["name"]}
- Type: {project["type"]}
- Stack: {", ".join(project["stack"])}
- Suggested skills: {skills}

## Startup Rule

Before editing a new or unfamiliar area:

1. State the objective.
2. Inspect the local files that govern the work.
3. Identify stack, constraints, risks, and verification.
4. Propose or execute the smallest useful next step.

Use `.vscode/jebat-workspace.json` and `PROJECT_START.md` as the repo capture record.
"""
