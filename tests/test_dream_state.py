"""Tests for the canonical dream state.

Dream state used to live in three places that disagreed at the same moment —
the engine file (`~/.jebat/dream_state.json`, 68 dreams), the workspace mirror
(`memory/.dream-state.json`, 52), and a CWD-relative CLI counter
(`.jebat/dream_state.json`, 2). These tests pin the reconciliation: one
authoritative file, with the mirror and the CLI as views of it.
"""

import json
from pathlib import Path

import pytest

from jebat.features.memory import automimpi
from jebat.features.memory.automimpi import load_dream_state, save_dream_state

pytestmark = pytest.mark.unit

EMPTY = {"sessions_since_dream": 0, "last_dream": None, "dream_count": 0}


@pytest.fixture
def state_file(tmp_path, monkeypatch):
    """Redirect the canonical state file into the test's temp dir."""
    target = tmp_path / "dream_state.json"
    monkeypatch.setattr(automimpi, "DREAM_STATE_FILE", target)
    return target


def test_missing_state_starts_fresh(state_file):
    assert load_dream_state() == EMPTY


def test_corrupt_or_non_dict_state_starts_fresh(state_file):
    state_file.write_text("{ not json", encoding="utf-8")
    assert load_dream_state() == EMPTY

    state_file.write_text("[1, 2, 3]", encoding="utf-8")
    assert load_dream_state() == EMPTY


def test_engine_schema_round_trips(state_file):
    save_dream_state(
        {"dream_count": 41, "last_dream": "2026-09-01T00:00:00+00:00", "sessions_since_dream": 2}
    )
    assert load_dream_state() == {
        "dream_count": 41,
        "last_dream": "2026-09-01T00:00:00+00:00",
        "sessions_since_dream": 2,
    }


def test_legacy_mirror_schema_is_normalized(state_file):
    """The old camelCase mirror must still load rather than silently reset."""
    state_file.write_text(
        json.dumps(
            {
                "lastDreamAt": "2026-09-21T11:36:01+00:00",
                "lastScanAt": "2026-09-21T11:36:01+00:00",
                "sessionsSinceDream": 4,
                "totalDreams": 52,
            }
        ),
        encoding="utf-8",
    )

    assert load_dream_state() == {
        "dream_count": 52,
        "last_dream": "2026-09-21T11:36:01+00:00",
        "sessions_since_dream": 4,
    }


def test_save_stamps_updated_at_and_leaves_no_temp_file(state_file, tmp_path):
    save_dream_state({"dream_count": 7, "last_dream": None, "sessions_since_dream": 0})

    raw = json.loads(state_file.read_text(encoding="utf-8"))
    assert raw["dream_count"] == 7
    assert raw["updated_at"]
    # Atomic write: the temp file is moved into place, never left behind.
    assert not (tmp_path / "dream_state.json.tmp").exists()


def test_automimpi_loads_and_persists_the_canonical_state(state_file, tmp_path):
    from jebat.features.memory import EnhancedMemorySystem

    save_dream_state(
        {"dream_count": 41, "last_dream": "2026-09-01T00:00:00+00:00", "sessions_since_dream": 0}
    )

    engine = automimpi.AutoMimpi(EnhancedMemorySystem(storage_path=tmp_path / "mem"))
    assert engine.dream_count == 41
    assert engine.last_dream_at is not None

    engine._save_state(sessions_since_dream=0)
    assert load_dream_state()["dream_count"] == 41


def test_workspace_mirror_reports_canonical_values_not_its_own(state_file, tmp_path, monkeypatch):
    """The mirror is a view — the drift that mattered was its stale counter."""
    from jebat.tools.automimpi_tools import _mirror_dream_state_to_workspace

    save_dream_state(
        {
            "dream_count": 68,
            "last_dream": "2026-09-28T08:44:41+00:00",
            "sessions_since_dream": 3,
        }
    )
    monkeypatch.chdir(tmp_path)

    path = _mirror_dream_state_to_workspace()

    assert Path(path) == tmp_path / "memory" / ".dream-state.json"
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["totalDreams"] == 68
    assert payload["lastDreamAt"] == "2026-09-28T08:44:41+00:00"
    assert payload["sessionsSinceDream"] == 3


def test_cli_gate_reads_the_canonical_state(state_file):
    """The session gate and /status must not keep a private counter."""
    save_dream_state(
        {"dream_count": 68, "last_dream": "2026-09-28T08:44:41+00:00", "sessions_since_dream": 3}
    )

    import jebat_cli_new.jebat as cli

    assert cli._load_dream_state() == {
        "dream_count": 68,
        "last_dream": "2026-09-28T08:44:41+00:00",
        "sessions_since_dream": 3,
    }
