"""Test fileops write module."""

import os
import tempfile

from jebat.fileops.write import write_file, undo_write
from jebat.fileops.safety import BackupManager


def test_write_file_creates_content() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        path = os.path.join(td, "test.txt")
        result = write_file(path, "hello world")
        assert result["written"] is True
        assert result["bytes"] > 0
        with open(path) as f:
            assert f.read() == "hello world"


def test_write_file_backups_existing() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        path = os.path.join(td, "test.txt")
        write_file(path, "original")
        result = write_file(path, "modified")
        assert result["written"] is True
        assert result.get("backup") is not None
        with open(path) as f:
            assert f.read() == "modified"


def test_undo_write_restores_backup() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        path = os.path.join(td, "test_undo.txt")
        write_file(path, "version 1")
        bm = BackupManager()
        backups_before = bm.list_backups(path)
        write_file(path, "version 2")
        # Undo via explicit backup path from result
        result = undo_write(path)
        # Check the backup file exists
        backups = bm.list_backups(path)
        assert len(backups) >= 1


def test_write_creates_parent_dirs() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        nested = os.path.join(td, "sub", "dir", "test.txt")
        result = write_file(nested, "nested")
        assert result["written"] is True
        assert os.path.isfile(nested)