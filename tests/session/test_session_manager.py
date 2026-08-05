"""Test session persistence manager."""

import os
import tempfile

from jebat.session.session_manager import SessionManager

import pytest

pytestmark = pytest.mark.unit


def test_session_manager_can_create_and_load_session() -> None:
    """Test that the session manager can create sessions, add messages, and load history."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        db_path = os.path.join(td, "sessions.db")
        sm = SessionManager(db_path)
        try:
            sid = sm.create_session(title="test")
            sm.add_message(sid, "user", "hello")
            sm.add_message(sid, "assistant", "hi")
            history = sm.load_history(sid, limit=10)
            assert len(history) == 2
            assert history[0]["role"] == "user"
            assert history[0]["content"] == "hello"
        finally:
            sm.conn.close()