"""Tests for the Agentix auto-solution foundry (deterministic paths only).

The model call is never exercised here: `auto_create(draft=...)` injects a
ready spec, and the pure helpers (extraction, slug, normalization) are tested
directly. Build/validation run through the shared agentix gates.
"""

import pytest

from jebat_cli_new.agentix import _build, _load_manifest
from jebat_cli_new.agentix_auto import (
    AgentixAutoError,
    _extract_json,
    auto_create,
    normalize_spec,
    slugify,
    write_solution,
)

OBJECTIVE = "summarize a folder of meeting notes into a weekly digest"

VALID_RAW = {
    "name": "meeting-digest",
    "description": (
        "Digests meeting notes into weekly summaries. Use for digest, notes "
        "summary, or weekly recap."
    ),
    "doctrine": (
        "# Meeting-digest doctrine\n\n"
        "Mission: turn raw notes into a factual weekly digest.\n\n"
        "Method:\n1. Read every note file in scope.\n2. Group entries by week.\n\n"
        "Output: write digest.md with per-week sections citing the source files."
    ),
    "tools": ["read_file", "write_file"],
    "max_iterations": 10,
    "jailed": True,
}


def test_extract_json_tolerates_fences_and_prose():
    reply = 'Sure!\n```json\n{"name": "x", "n": 1}\n```\nDone.'
    assert _extract_json(reply) == {"name": "x", "n": 1}


def test_extract_json_rejects_garbage():
    with pytest.raises(AgentixAutoError):
        _extract_json("no json here")
    with pytest.raises(AgentixAutoError):
        _extract_json('{"broken": ')


def test_slugify_and_name_normalization():
    assert slugify("Meeting Digest!!") == "meeting-digest"
    assert slugify("123 notes") == "auto-123-notes"
    spec = normalize_spec(dict(VALID_RAW, name="Weird Name"), OBJECTIVE)
    assert spec["name"] == "weird-name"
    spec = normalize_spec(dict(VALID_RAW, name="ignored"), OBJECTIVE, name_override="My Override!")
    assert spec["name"] == "my-override"


def test_normalize_spec_filters_tools_and_clamps_iterations():
    raw = dict(VALID_RAW, tools=["read_file", "rm", "read_file"], max_iterations=99)
    spec = normalize_spec(raw, OBJECTIVE)
    assert spec["tools"] == ["read_file"]
    assert spec["max_iterations"] == 20
    raw = dict(VALID_RAW, tools=["nope"], max_iterations="x")
    spec = normalize_spec(raw, OBJECTIVE)
    assert spec["tools"] == ["read_file", "search_files", "terminal", "write_file", "list_dir"]
    assert spec["max_iterations"] == 12


def test_normalize_spec_refuses_thin_doctrine():
    with pytest.raises(AgentixAutoError):
        normalize_spec(dict(VALID_RAW, doctrine="too short"), OBJECTIVE)


def test_write_solution_roundtrip(tmp_path):
    spec = normalize_spec(VALID_RAW, OBJECTIVE)
    sol = write_solution(spec, tmp_path)
    assert (sol / "agentix.yaml").is_file()
    assert (sol / "agent.md").is_file()
    assert (sol / "workspace" / ".gitkeep").is_file()
    mf = _load_manifest(sol)
    assert mf["name"] == "meeting-digest"
    assert mf["runtime"] == "llm"
    assert mf["llm_workspace"] == "workspace"
    info = _build(sol)
    assert info["manifest_sha256"]


def test_auto_create_with_injected_draft(tmp_path):
    outcome = auto_create(OBJECTIVE, target_dir=tmp_path, draft=VALID_RAW)
    assert outcome["spec"]["name"] == "meeting-digest"
    assert outcome["build"]["manifest_sha256"]
    assert outcome["deploy"] is None
    assert (tmp_path / "meeting-digest" / ".agentix" / "build.json").is_file()
    # Second run must not clobber the first.
    with pytest.raises(AgentixAutoError):
        auto_create(OBJECTIVE, target_dir=tmp_path, draft=VALID_RAW)


def test_auto_create_rejects_unknown_deploy_before_writing(tmp_path):
    with pytest.raises(AgentixAutoError):
        auto_create(OBJECTIVE, target_dir=tmp_path, deploy="vps", draft=VALID_RAW)
    assert list(tmp_path.iterdir()) == []
