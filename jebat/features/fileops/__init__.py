"""JEBAT File Operations — read, write, patch, search, diff, undo."""

from __future__ import annotations


async def read_file(path: str, offset: int = 1, limit: int = 500) -> dict:
    ...


async def write_file(path: str, content: str, force: bool = False) -> dict:
    ...


async def patch_file(path: str, old: str, new: str, replace_all: bool = False) -> dict:
    ...


async def search_files(pattern: str, path: str = ".", file_glob: str | None = None, limit: int = 50) -> dict:
    ...