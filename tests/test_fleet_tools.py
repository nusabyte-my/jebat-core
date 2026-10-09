"""Tests for the NusaByte fleet bus tools (deterministic, temp root)."""

import textwrap

import pytest

from jebat.tools import fleet_tools


@pytest.fixture()
def fleet_root(tmp_path, monkeypatch):
    """Minimal nusabyte-hermes tree: registry + two queues with all stages."""
    root = tmp_path / "nusabyte-hermes"
    (root / "bus" / "registry").mkdir(parents=True)
    (root / "bus" / "registry" / "agents.yaml").write_text(
        textwrap.dedent(
            """\
            agents:
              nusabyte-finance:
                codename: "Tun Mutahir"
                role: "invoicing (JEBAT: Bendahara)"
                task_queue: {root}/bus/tasks/finance
                docs: {root}/agents/nusabyte-finance
                gateway_url: http://127.0.0.1:18929 (planned)
                allowed_work:
                  - draft invoices
                forbidden_work:
                  - auto-submitting to MyInvois
              nusabyte-docs:
                codename: "Tun Seri Lanang"
                role: "docs"
                task_queue: {root}/bus/tasks/docs
                docs: {root}/agents/nusabyte-docs
            """
        ).format(root=root.as_posix()),
        encoding="utf-8",
    )
    for queue in ("finance", "docs"):
        for stage in fleet_tools.STAGES:
            (root / "bus" / "tasks" / queue / stage).mkdir(parents=True)
    monkeypatch.setenv("NUSABYTE_FLEET_ROOT", str(root))
    return root


def test_fleet_agents_lists_registry(fleet_root):
    import asyncio

    out = asyncio.run(fleet_tools.fleet_agents())
    assert out["count"] == 2
    finance = next(a for a in out["agents"] if a["slug"] == "nusabyte-finance")
    assert finance["codename"] == "Tun Mutahir"
    assert finance["queue"] == "finance"
    assert "auto-submitting to MyInvois" in finance["forbidden_work"]


def test_fleet_tasks_counts_and_lists(fleet_root):
    import asyncio

    (fleet_root / "bus" / "tasks" / "finance" / "inbox" / "TASK-2026-10-09-001-x.md").write_text(
        "task", encoding="utf-8"
    )
    bus = asyncio.run(fleet_tools.fleet_tasks())
    assert bus["queues_with_tasks"]["finance"]["inbox"] == 1
    assert bus["totals"]["inbox"] == 1

    one = asyncio.run(fleet_tools.fleet_tasks(agent="finance", stage="inbox"))
    assert one["files"] == ["TASK-2026-10-09-001-x.md"]

    by_slug = asyncio.run(fleet_tools.fleet_tasks(agent="nusabyte-finance"))
    assert by_slug["agent"] == "nusabyte-finance"
    assert by_slug["stages"]["inbox"] == ["TASK-2026-10-09-001-x.md"]


def test_fleet_dispatch_writes_brief(fleet_root):
    import asyncio

    out = asyncio.run(
        fleet_tools.fleet_dispatch(
            agent="nusabyte-finance",
            title="Draft March invoices for NB clients",
            context="Ledger at /opt/data/bin/nb-ledger; drafts only.",
            requires_approval_before=["sending invoices"],
        )
    )
    assert "error" not in out
    assert out["agent"] == "nusabyte-finance"
    assert out["queue"] == "finance"
    assert out["task_id"].startswith("TASK-")
    body = open(out["path"], encoding="utf-8").read()
    assert "created_by: jebat-agentix" in body
    assert "assigned_to: nusabyte-finance" in body
    assert "status: ready" in body
    assert "- publishing" in body and "- sending invoices" in body
    assert "# Task" in body and "# Expected Output" in body


def test_fleet_dispatch_increments_bus_global_id(fleet_root):
    import asyncio

    first = asyncio.run(fleet_tools.fleet_dispatch(agent="finance", title="a"))
    second = asyncio.run(fleet_tools.fleet_dispatch(agent="docs", title="b"))
    assert first["task_id"] != second["task_id"]
    n1 = int(first["task_id"].rsplit("-", 1)[1])
    n2 = int(second["task_id"].rsplit("-", 1)[1])
    assert n2 == n1 + 1


def test_fleet_dispatch_rejects_unknown_agent(fleet_root):
    import asyncio

    out = asyncio.run(fleet_tools.fleet_dispatch(agent="nusabyte-nope", title="x"))
    assert "error" in out
    assert "unknown agent" in out["error"]


def test_fleet_missing_root_reports_error(tmp_path, monkeypatch):
    import asyncio

    monkeypatch.setenv("NUSABYTE_FLEET_ROOT", str(tmp_path / "nowhere"))
    out = asyncio.run(fleet_tools.fleet_agents())
    assert "error" in out
    assert "NUSABYTE_FLEET_ROOT" in out["error"]
