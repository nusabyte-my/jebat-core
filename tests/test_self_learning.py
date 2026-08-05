"""Tests for the Self-Learning subsystem (MetaLearner + AlertManager)."""

import pytest

from jebat.features.self_learning import (
    AlertManager,
    AlertRule,
    AlertSeverity,
    MetaLearner,
)

pytestmark = pytest.mark.unit


def test_meta_learner_registers_builtin_strategies():
    ml = MetaLearner()
    assert len(ml.strategies) >= 4


def test_meta_learner_ucb_selection_and_outcome():
    ml = MetaLearner()
    ctx = {"task": "complex optimization problem"}
    strategy = ml.get_best_strategy(ctx)
    assert strategy is not None

    ml.record_outcome(strategy.strategy_id, reward=1.0, context=ctx)
    assert ml.strategies[strategy.strategy_id].usage_count == 1
    assert ml.strategies[strategy.strategy_id].success_rate > 0


def test_meta_learner_performance_summary():
    ml = MetaLearner()
    first_id = next(iter(ml.strategies))
    ml.record_outcome(first_id, reward=1.0, context={"x": 1})
    summary = ml.get_performance_summary()
    assert "total_strategies" in summary
    assert summary["total_strategies"] >= 4


def test_alert_manager_evaluate_no_crash():
    # Regression: AlertManager.evaluate uses time.time() and logging, which were
    # previously not imported (would raise NameError).
    am = AlertManager()
    am.add_rule(
        AlertRule(name="TestAlert", expr="metric_cpu > 0.5", severity=AlertSeverity.WARNING)
    )

    def query_fn(expr):
        return {"data": {"result": [{"value": [123, "0.9"]}]}}

    fired = am.evaluate(query_fn)
    assert len(fired) == 1
    assert am.get_active_alerts()
    summary = am.get_alert_summary()
    assert summary["warning"] >= 1


def test_self_learning_agent_alias_exists():
    from jebat.features.self_learning import create_self_learning_agent

    assert callable(create_self_learning_agent)
