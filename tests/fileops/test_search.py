"""Test fileops search module."""

import os
import tempfile

from jebat.fileops.search import search_files

import pytest

pytestmark = pytest.mark.unit


def test_search_content_finds_match() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        path = os.path.join(td, "test.txt")
        with open(path, "w") as f:
            f.write("hello world\ngoodbye\n")
        result = search_files("hello", target="content", path=td)
        assert len(result["matches"]) >= 1
        assert result["matches"][0]["line"] == 1


def test_search_files_by_name() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        path = os.path.join(td, "my_module.py")
        with open(path, "w") as f:
            f.write("x = 1\n")
        result = search_files("*.py", target="files", path=td)
        assert len(result["matches"]) >= 1
        assert "my_module.py" in result["matches"][0]["path"]


def test_search_content_no_match_returns_empty() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        path = os.path.join(td, "test.txt")
        with open(path, "w") as f:
            f.write("hello\n")
        result = search_files("zzzNOTFOUNDxxx", target="content", path=td)
        assert result["matches"] == []