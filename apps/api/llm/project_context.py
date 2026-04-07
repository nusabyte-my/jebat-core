from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProjectContext:
    root: str
    summary: str


def build_project_context(project_path: str | Path, max_files: int = 12) -> ProjectContext:
    root = Path(project_path).resolve()
    files = _interesting_files(root, max_files=max_files)
    lines = [
        f"Project root: {root}",
        f"Detected files ({len(files)} shown):",
    ]
    for item in files:
        lines.append(f"- {item}")
    return ProjectContext(root=str(root), summary="\n".join(lines))


def _interesting_files(root: Path, max_files: int) -> list[str]:
    candidates: list[str] = []
    for pattern in (
        "README.md",
        "pyproject.toml",
        "package.json",
        "requirements.txt",
        ".env.example",
        ".jebatrc.json",
    ):
        target = root / pattern
        if target.exists():
            candidates.append(str(target.relative_to(root)))

    for path in sorted(root.rglob("*")):
        if len(candidates) >= max_files:
            break
        if not path.is_file():
            continue
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        rel = str(path.relative_to(root))
        if rel not in candidates:
            candidates.append(rel)
    return candidates[:max_files]
