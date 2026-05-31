"""Test fileops modules."""

import os
import tempfile

from jebat.fileops.read import read_file


def test_file_read_returns_lines_with_numbers() -> None:
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".txt") as tf:
        tf.write("line1\nline2\nline3\n")
        tf.flush()
        tf_path = tf.name
    try:
        result = read_file(tf_path, offset=1, limit=2)
        assert result["content"] == "1|line1\n2|line2"
        assert result["total_lines"] == 3
    finally:
        os.unlink(tf_path)


def test_file_read_nonexistent_returns_error() -> None:
    result = read_file("/nonexistent/path.txt")
    assert "error" in result


def test_file_read_offset_past_end() -> None:
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".txt") as tf:
        tf.write("line1\n")
        tf.flush()
        tf_path = tf.name
    try:
        result = read_file(tf_path, offset=5, limit=10)
        assert result["content"] == ""
        assert result["total_lines"] == 1
    finally:
        os.unlink(tf_path)