"""Unit tests for the JEBAT Workflow Engine (orchestration subsystem)."""

import asyncio

import pytest

from jebat.orchestration.workflow_engine import (
    TaskStatus,
    WorkflowEngine,
    WorkflowStatus,
)

pytestmark = pytest.mark.unit


def test_create_workflow_registers():
    eng = WorkflowEngine()
    wf = eng.create_workflow("Demo", "desc")
    assert wf.id in eng.workflows
    assert wf.name == "Demo"
    assert wf.status == WorkflowStatus.DRAFT


def test_add_task_unknown_workflow_raises():
    eng = WorkflowEngine()
    with pytest.raises(ValueError):
        eng.add_task("missing", "t1", "Task", lambda: 1)


def test_execute_linear_dag_orders_tasks():
    eng = WorkflowEngine()
    wf = eng.create_workflow("linear")

    order = []

    def make(step):
        def fn():
            order.append(step)
            return step

        return fn

    a = eng.add_task(wf.id, "a", "A", make("a"))
    b = eng.add_task(wf.id, "b", "B", make("b"), dependencies=["a"])
    c = eng.add_task(wf.id, "c", "C", make("c"), dependencies=["b"])

    result = asyncio.run(eng.execute_workflow(wf.id))
    assert result["status"] == "success"
    assert order == ["a", "b", "c"]
    assert c.status == TaskStatus.COMPLETED
    assert result["completed_tasks"] == 3


def test_execute_parallel_branch_dependency():
    eng = WorkflowEngine()
    wf = eng.create_workflow("branch")

    results = {}

    def make(step):
        def fn():
            results[step] = True
            return step

        return fn

    root = eng.add_task(wf.id, "root", "Root", make("root"))
    x = eng.add_task(wf.id, "x", "X", make("x"), dependencies=["root"])
    y = eng.add_task(wf.id, "y", "Y", make("y"), dependencies=["root"])

    result = asyncio.run(eng.execute_workflow(wf.id))
    assert result["status"] == "success"
    assert set(results) == {"root", "x", "y"}
    assert x.status == TaskStatus.COMPLETED and y.status == TaskStatus.COMPLETED


def test_dependency_failure_skips_downstream():
    eng = WorkflowEngine()
    wf = eng.create_workflow("fail")

    def good():
        return "ok"

    def bad():
        raise RuntimeError("boom")

    a = eng.add_task(wf.id, "a", "A", bad)
    b = eng.add_task(wf.id, "b", "B", good, dependencies=["a"])

    result = asyncio.run(eng.execute_workflow(wf.id))
    assert result["status"] == "failed"
    assert a.status == TaskStatus.FAILED
    assert b.status == TaskStatus.SKIPPED
    assert result["failed_tasks"] == 1


def test_execute_unknown_workflow_returns_error():
    eng = WorkflowEngine()
    assert asyncio.run(eng.execute_workflow("nope")) == {"error": "Workflow not found"}


def test_dependency_result_injected_when_accepted():
    eng = WorkflowEngine()
    wf = eng.create_workflow("inj")

    eng.add_task(wf.id, "a", "A", lambda: 42)
    eng.add_task(wf.id, "b", "B", lambda **kwargs: kwargs["_a_result"], dependencies=["a"])

    result = asyncio.run(eng.execute_workflow(wf.id))
    assert result["status"] == "success"
    assert result["results"]["b"] == 42


def test_task_timeout_raises():
    eng = WorkflowEngine()
    wf = eng.create_workflow("to")

    async def slow():
        await asyncio.sleep(0.2)
        return "done"

    t = eng.add_task(wf.id, "s", "Slow", slow)
    t.timeout = 0

    result = asyncio.run(eng.execute_workflow(wf.id))
    assert result["status"] == "failed"
    assert t.status == TaskStatus.FAILED


def test_get_workflow_status_and_visualize():
    eng = WorkflowEngine()
    wf = eng.create_workflow("viz")
    eng.add_task(wf.id, "a", "A", lambda: 1)
    eng.add_task(wf.id, "b", "B", lambda: 2, dependencies=["a"])

    status = eng.get_workflow_status(wf.id)
    assert status["total_tasks"] == 2
    assert status["status"] == WorkflowStatus.DRAFT.value

    dot = eng.visualize_workflow(wf.id)
    assert "digraph workflow" in dot
    assert '"a" -> "b"' in dot
    assert eng.visualize_workflow("missing") == ""
