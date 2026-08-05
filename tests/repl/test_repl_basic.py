"""Test REPL basics."""

import os
import tempfile

from jebat.repl.repl_session import ReplSession

import pytest

pytestmark = pytest.mark.unit


def test_repl_session_can_store_and_load() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        db = os.path.join(td, "sessions.db")
        sess = ReplSession(db_path=db)
        sid = sess.create_or_load("test-repl")
        assert sid
        sess.add_message("user", "hello")
        sess.add_message("assistant", "world")
        history = sess.load_history(limit=10)
        assert len(history) == 2
        assert history[0]["content"] == "hello"
        assert history[1]["content"] == "world"


def test_repl_session_autoname() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        db = os.path.join(td, "sessions.db")
        sess = ReplSession(db_path=db)
        sid = sess.create_or_load()  # no name → auto-generated
        assert sid
        assert sess.name  # should be auto-generated