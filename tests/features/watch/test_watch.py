"""Tests for File Watcher."""

import asyncio
import os
import tempfile
import time
from pathlib import Path

import pytest

from jebat.features.watch.watch import (
    WatchConfig,
    FileWatcher,
    AsyncFileWatcher,
    create_default_watcher,
    WATCHDOG_AVAILABLE,
)


@pytest.mark.skipif(not WATCHDOG_AVAILABLE, reason="watchdog not installed")
class TestFileWatcher:
    def test_watch_config_defaults(self):
        config = WatchConfig()
        assert config.paths == ["."]
        assert "*.py" in config.patterns
        assert "*.md" in config.patterns
        assert config.debounce_ms == 300
        assert config.recursive is True

    def test_create_default_watcher(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = create_default_watcher(tmpdir)
            assert isinstance(watcher, FileWatcher)
            assert watcher.config.paths == [tmpdir]

    def test_file_watcher_start_stop(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = WatchConfig(paths=[tmpdir], debounce_ms=50)
            watcher = FileWatcher(config)
            watcher.start()
            assert watcher._running
            watcher.stop()
            assert not watcher._running

    def test_file_watcher_callback(self):
        events = []

        def callback(path: str, event_type: str):
            events.append((path, event_type))

        with tempfile.TemporaryDirectory() as tmpdir:
            config = WatchConfig(paths=[tmpdir], debounce_ms=50)
            watcher = FileWatcher(config)
            watcher.add_callback(callback)
            watcher.start()

            # Create a file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('hello')")

            # Wait for event
            time.sleep(0.2)

            watcher.stop()

            assert len(events) >= 1
            assert any("created" in e[1] or "modified" in e[1] for e in events)

    def test_async_file_watcher(self):
        async def run_test():
            events = []

            with tempfile.TemporaryDirectory() as tmpdir:
                config = WatchConfig(paths=[tmpdir], debounce_ms=50)
                async_watcher = AsyncFileWatcher(config)
                async_watcher.start()

                # Create a file
                test_file = Path(tmpdir) / "async_test.py"
                test_file.write_text("print('async')")

                # Wait for event
                await asyncio.sleep(0.2)

                # Get events from queue
                while not async_watcher.queue.empty():
                    events.append(async_watcher.queue.get_nowait())

                async_watcher.stop()

            assert len(events) >= 1

        asyncio.run(run_test())

    def test_debouncing(self):
        events = []

        def callback(path: str, event_type: str):
            events.append((path, event_type))

        with tempfile.TemporaryDirectory() as tmpdir:
            config = WatchConfig(paths=[tmpdir], debounce_ms=200)
            watcher = FileWatcher(config)
            watcher.add_callback(callback)
            watcher.start()

            test_file = Path(tmpdir) / "debounce.py"
            test_file.write_text("v1")
            time.sleep(0.05)
            test_file.write_text("v2")
            time.sleep(0.05)
            test_file.write_text("v3")
            time.sleep(0.3)  # Wait for debounce

            watcher.stop()

            # Should only get 1 event due to debouncing
            assert len(events) == 1

    def test_ignore_patterns(self):
        events = []

        def callback(path: str, event_type: str):
            events.append((path, event_type))

        with tempfile.TemporaryDirectory() as tmpdir:
            config = WatchConfig(
                paths=[tmpdir],
                debounce_ms=50,
                ignore_patterns=["*.log", "__pycache__"]
            )
            watcher = FileWatcher(config)
            watcher.add_callback(callback)
            watcher.start()

            # Create ignored files
            Path(tmpdir) / "debug.log"
            (Path(tmpdir) / "debug.log").write_text("log")
            (Path(tmpdir) / "test.pyc").write_text("bytecode")

            # Create watched file
            (Path(tmpdir) / "valid.py").write_text("print('hi')")

            time.sleep(0.2)
            watcher.stop()

            # Should only get event for valid.py
            assert len(events) == 1
            assert "valid.py" in events[0][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
