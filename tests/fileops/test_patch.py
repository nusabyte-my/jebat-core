"""Test fileops patch module."""

import os
import tempfile

from jebat.fileops.patch import patch_file

import pytest

pytestmark = pytest.mark.unit


def test_patch_single_replacement() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        path = os.path.join(td, "test.txt")
        with open(path, "w") as f:
            f.write("hello world\n")
        result = patch_file(path, "hello", "goodbye")
        assert result["patched"] is True
        assert result["matches"] == 1
        with open(path) as f:
            assert f.read() == "goodbye world\n"


def test_patch_duplicate_without_replace_all_errors() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        path = os.path.join(td, "test.txt")
        with open(path, "w") as f:
            f.write("hello\nhello\n")
        result = patch_file(path, "hello", "hi", replace_all=False)
        assert "error" in result
        assert "matches 2" in result["error"]


def test_patch_replace_all() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        path = os.path.join(td, "test.txt")
        with open(path, "w") as f:
            f.write("hello\nhello\n")
        result = patch_file(path, "hello", "hi", replace_all=True)
        assert result["patched"] is True
        assert result["matches"] == 2
        with open(path) as f:
            assert f.read() == "hi\nhi\n"


def test_patch_not_found_errors() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        path = os.path.join(td, "test.txt")
        with open(path, "w") as f:
            f.write("hello\n")
        result = patch_file(path, "notfound", "x")
        assert "error" in result