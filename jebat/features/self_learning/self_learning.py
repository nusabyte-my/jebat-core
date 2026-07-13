"""
Meta-Learner - Learns how to learn

Monitors learning process, adapts strategies, optimizes hyperparameters
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from collections import defaultdict
from collections.abc import AsyncIterator

import numpy as np


class LearningStrategy(Enum):
    """Learning strategies the agent can use"""
    EXPLORATION = "exploration"       # Try new approaches
    EXPLOITATION = "exploitation"     # Use known good strategies
    IMITATION = "imitation"           # Copy successful patterns
    CURIOUSITY = "curiosity"          # Seek novel experiences
    REFLECTIVE = "reflective"         # Analyze past performance
    ADVERSARIAL = "adversarial"       # Stress-test own capabilities


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PerformanceMetric(Enum):
    """Metrics for evaluating performance"""
    SUCCESS_RATE = "success_rate"
    TOKEN_EFFICIENCY = "token_efficiency"
    TIME_EFFICIENCY = "time_efficiency"
    QUALITY_SCORE = "quality_score"
    USER_SATISFACTION = "user_satisfaction"
    ERROR_RATE = "error_rate"
    COST_EFFICIENCY = "cost_efficiency"
    INNOVATION_SCORE = "innovation_score"


@dataclass
class LearningExperience:
    """A single learning experience"""
    experience_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    task_description: str = ""
    strategy_used: str = ""
    context: Dict = field(default_factory=dict)
    actions_taken: List[str] = field(default_factory=list)
    outcome: str = ""
    success: bool = False
    metrics: Dict[PerformanceMetric, float] = field(default_factory=dict)
    reward: float = 0.0
    lessons_learned: List[str] = field(default_factory=list)
    strategy_adjustments: List[str] = field(default_factory=list)
    dream_inspired: bool = False


@dataclass
class Strategy:
    """A learned strategy"""
    strategy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    applicable_contexts: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    expected_outcomes: List[str] = field(default_factory=list)
    success_rate: float = 0.5
    usage_count: int = 0
    avg_reward: float = 0.0
    last_used: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Set[str] = field(default_factory=set)
    parent_strategy: Optional[str] = None  # For strategy evolution
    confidence: float = 0.5


@dataclass
class LearningGoal:
    """A learning objective"""
    goal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    target_metric: PerformanceMetric = PerformanceMetric.SUCCESS_RATE
    target_value: float = 0.8
    current_value: float = 0.0
    priority: int = 1
    deadline: Optional[datetime] = None
    strategies_tried: List[str] = field(default_factory=list)
    progress: float = 0.0
    status: str = "active"  # active, achieved, abandoned
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MetaLearner:
    """
    Meta-Learner - Learns how to learn
    
    Monitors learning process, adapts strategies, optimizes hyperparameters
    """

    def __init__(self, memory_system = None):
        self.strategies: Dict[str, Strategy] = {}
        self.experiences: List = []
        self.goals: Dict[str, LearningGoal] = {}
        self.performance_history: List[Dict] = []
        
        # Meta-parameters
        self.exploration_rate = 0.2
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        
        # Strategy performance tracking
        self.strategy_rewards: Dict[str, List[float]] = defaultdict(list)
        self.context_strategy_map: Dict[str, str] = {}  # context -> best strategy
        
        # Meta-learning
        self.meta_learning_enabled = True
        self.adaptation_rate = 0.1
        
        # Auto-register builtin strategies
        for s in BUILTIN_STRATEGIES:
            self.register_strategy(s)

    def register_strategy(self, strategy: Strategy):
        self.strategies[strategy.strategy_id] = strategy

    def get_best_strategy(self, context: Dict) -> Optional[Strategy]:
        """Select best strategy for context"""
        context_key = self._context_to_key(context)
        
        # Check if we have a known good strategy for this context
        if context_key in self.context_strategy_map:
            strategy_id = self.context_strategy_map[context_key]
            if strategy_id in self.strategies:
                return self.strategies[strategy_id]
        
        # Otherwise, use UCB-like selection
        applicable = [s for s in self.strategies.values() if self._is_applicable(s, context)]
        if not applicable:
            return None
        
        # UCB1 selection
        total_uses = sum(s.usage_count for s in applicable)
        best = None
        best_score = -1
        
        for strategy in applicable:
            if strategy.usage_count == 0:
                return strategy  # Try unused strategies
            
            exploitation = strategy.success_rate
            exploration = np.sqrt(2 * np.log(total_uses) / strategy.usage_count)
            score = exploitation + self.exploration_rate * exploration
            
            if score > best_score:
                best_score = score
                best = strategy
        
        return best

    def record_outcome(self, strategy_id: str, reward: float, context: Dict):
        """Record outcome of using a strategy"""
        if strategy_id in self.strategies:
            strategy = self.strategies[strategy_id]
            strategy.usage_count += 1
            strategy.last_used = datetime.now(timezone.utc)
            
            # Update running average
            n = strategy.usage_count
            strategy.success_rate = ((n - 1) * strategy.success_rate + (1 if reward > 0 else 0)) / n
            strategy.avg_reward = ((n - 1) * strategy.avg_reward + reward) / n
            strategy.last_updated = datetime.now(timezone.utc)
            
            # Track rewards
            self.strategy_rewards[strategy_id].append(reward)
            
            # Update context mapping
            context_key = self._context_to_key(context)
            if reward > 0:
                self.context_strategy_map[context_key] = strategy_id

    def _context_to_key(self, context: Dict) -> str:
        """Convert context to lookup key"""
        # Simple hashing - in practice would use embeddings
        items = sorted(context.items())
        return str(hash(tuple(sorted(items))) % 10000)

    def _is_applicable(self, strategy: Strategy, context: Dict) -> bool:
        if not strategy.applicable_contexts:
            return True
        # Simple check - in practice would use embeddings
        context_str = str(context).lower()
        return any(c.lower() in context_str for c in strategy.applicable_contexts)

    def add_experience(self, experience: 'LearningExperience'):
        self.experiences.append(experience)
        
        # Keep recent experiences
        if len(self.experiences) > 10000:
            self.experiences = self.experiences[-5000:]

    def get_performance_summary(self) -> Dict:
        """Get performance summary across all strategies"""
        return {
            "total_experiences": len(self.experiences),
            "total_strategies": len(self.strategies),
            "avg_success_rate": np.mean([s.success_rate for s in self.strategies.values()]) if self.strategies else 0,
            "best_strategy": max(self.strategies.values(), key=lambda s: s.success_rate).name if self.strategies else None,
            "active_goals": len([g for g in self.goals.values() if g.status == "active"]),
        }

    def set_goal(self, goal: 'LearningGoal'):
        self.goals[goal.goal_id] = goal

    def update_goal_progress(self, goal_id: str, current_value: float):
        if goal_id in self.goals:
            self.goals[goal_id].current_value = current_value
            self.goals[goal_id].progress = min(1.0, current_value / self.goals[goal_id].target_value)
            if self.goals[goal_id].progress >= 1.0:
                self.goals[goal_id].status = "achieved"

    def adapt_hyperparameters(self, recent_performance: float):
        """Meta-learning: adapt hyperparameters based on performance"""
        if not self.meta_learning_enabled:
            return
        
        if recent_performance < 0.4:
            # Poor performance - increase exploration
            self.exploration_rate = min(0.5, self.exploration_rate * 1.1)
            self.learning_rate = min(0.3, self.learning_rate * 1.05)
        elif recent_performance > 0.8:
            # Good performance - exploit more
            self.exploration_rate = max(0.05, self.exploration_rate * 0.95)
            self.learning_rate = max(0.01, self.learning_rate * 0.98)

BUILTIN_STRATEGIES = [
    Strategy(
        name="divide_and_conquer",
        description="Break complex problems into smaller subproblems",
        applicable_contexts=["complex", "multi-step", "large", "problem", "task", "optimize", "database", "query", "optimization", "design", "architecture"],
        steps=["Analyze problem", "Decompose", "Solve subproblems", "Integrate"],
        expected_outcomes=["complete solution", "modular components"],
    ),
    Strategy(
        name="iterative_refinement",
        description="Start simple, iteratively improve",
        applicable_contexts=["uncertain", "evolving", "prototype", "iterative", "improve", "refine", "optimize", "tune", "debug"],
        steps=["Create MVP", "Test", "Gather feedback", "Refine"],
        expected_outcomes=["working solution", "validated assumptions"],
    ),
    Strategy(
        name="first_principles",
        description="Break down to fundamental principles",
        applicable_contexts=["novel", "unprecedented", "fundamental", "new", "design", "architecture", "algorithm"],
        steps=["Identify axioms", "Derive from basics", "Build up", "Validate"],
        expected_outcomes=["deep understanding", "novel solutions"],
    ),
    Strategy(
        name="analogical_reasoning",
        description="Apply solutions from similar domains",
        applicable_contexts=["similar_problem_exists", "cross_domain", "pattern", "analogy", "reuse", "transfer"],
        steps=["Find analogies", "Map principles", "Adapt solution", "Validate"],
        expected_outcomes=["novel approach", "proven pattern"],
    ),
]

DEFAULT_ALERT_RULES = []


class WebhookNotifier:
    """Webhook notifier"""
    pass


class SlackNotifier:
    """Slack notifier"""
    pass


class PagerDutyNotifier:
    """PagerDuty notifier"""
    pass


DEFAULT_ALERT_RULES = []


# ─── Alert Config ──────────────────────────────────────────────

@dataclass
class AlertRule:
    """Alert rule definition (PrometheusRule compatible)."""
    name: str
    expr: str
    severity: str
    for_duration: str = "5m"
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)

    def to_prometheus_rule(self) -> dict[str, Any]:
        """Convert to PrometheusRule format."""
        return {
            "alert": self.name,
            "expr": self.expr,
            "for": self.for_duration,
            "labels": {
                "severity": self.severity,
                **self.labels,
            },
            "annotations": self.annotations,
        }


# ─── Alert Manager ──────────────────────────────────────────────

@dataclass
class Alert:
    """Fired alert instance."""
    rule: AlertRule
    value: float
    labels: dict[str, str]
    annotations: dict[str, str]
    fired_at: float
    status: str = "firing"  # firing, resolved


class AlertManager:
    """Manages alert evaluation and notification."""

    def __init__(self, evaluation_interval: float = 30.0):
        self.rules: list[AlertRule] = []
        self.active_alerts: dict[str, 'Alert'] = {}
        self.notifiers: list[Callable[[Alert], None]] = []
        self.evaluation_interval = evaluation_interval

    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self.rules.append(rule)

    def add_notifier(self, notifier: Callable[['Alert'], None]) -> None:
        """Add a notification callback."""
        self.notifiers.append(notifier)

    def evaluate(self, query_fn: Callable[[str], dict[str, Any]]) -> list['Alert']:
        """Evaluate all rules against Prometheus queries."""
        fired = []

        for rule in self.rules:
            try:
                result = query_fn(rule.expr)
                # result should be: {"metric": {...}, "value": [timestamp, value]}
                for series in result.get("data", {}).get("result", []):
                    value = float(series["value"][1])
                    labels = series.get("metric", {})

                    alert_key = f"{rule.name}:{json.dumps(labels, sort_keys=True)}"

                    if alert_key not in self.active_alerts:
                        # New alert
                        alert = Alert(
                            rule=rule,
                            value=value,
                            labels=labels,
                            annotations=self._render_annotations(rule, labels, value),
                            fired_at=time.time(),
                        )
                        self.active_alerts[alert_key] = alert
                        fired.append(alert)
                        self._notify(alert)
                    else:
                        # Update existing
                        self.active_alerts[alert_key].value = value
            except Exception as e:
                logging.getLogger(__name__).error(f"Alert evaluation failed for {rule.name}: {e}")

        return fired

    def _render_annotations(self, rule: AlertRule, labels: dict, value: float) -> dict[str, str]:
        """Render annotation templates."""
        context = {"labels": labels, "value": value}
        rendered = {}
        for k, v in rule.annotations.items():
            try:
                rendered[k] = v.format(**context)
            except Exception:
                rendered[k] = v
        return rendered

    def _notify(self, alert: 'Alert') -> None:
        """Send notifications for alert."""
        for notifier in self.notifiers:
            try:
                notifier(alert)
            except Exception as e:
                logging.getLogger(__name__).error(f"Notifier failed: {e}")

    def get_active_alerts(self) -> list['Alert']:
        """Get all currently firing alerts."""
        return list(self.active_alerts.values())

    def get_alert_summary(self) -> dict[str, int]:
        """Get alert counts by severity."""
        summary = {s.value: 0 for s in AlertSeverity}
        for alert in self.active_alerts.values():
            summary[alert.rule.severity.value] += 1
        return summary


# ─── Built-in Alert Rules ────────────────────────────────────────

BUILTIN_ALERT_RULES = [
    # LLM Alerts
    AlertRule(
        name="LLMHighLatency",
        expr='histogram_quantile(0.99, sum(rate(jebat_llm_duration_seconds_bucket[5m])) by (le, provider, model)) > 30',
        severity=AlertSeverity.CRITICAL,
        for_duration="5m",
        labels={"component": "llm", "team": "platform"},
        annotations={
            "summary": "LLM p99 latency > 30s for {{ $labels.provider }}/{{ $labels.model }}",
            "description": "LLM provider {{ $labels.provider }} model {{ $labels.model }} has p99 latency of {{ $value }}s",
            "runbook": "https://runbooks.jebat.ai/llm-high-latency",
        },
    ),
    AlertRule(
        name="LLMHighErrorRate",
        expr='sum(rate(jebat_llm_requests_total{status="error"}[5m])) by (provider, model) / sum(rate(jebat_llm_requests_total[5m])) by (provider, model) > 0.05',
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "llm", "team": "platform"},
        annotations={
            "summary": "LLM error rate > 5% for {{ $labels.provider }}/{{ $labels.model }}",
            "description": "Error rate is {{ $value | humanizePercentage }} for {{ $labels.provider }}/{{ $labels.model }}",
        },
    ),
    AlertRule(
        name="LLMHighCost",
        expr='increase(jebat_llm_cost_usd_total[1h]) > 100',
        severity=AlertSeverity.WARNING,
        for_duration="1h",
        labels={"component": "llm", "team": "finance"},
        annotations={
            "summary": "LLM cost > $100/hour for {{ $labels.provider }}/{{ $labels.model }}",
        },
    ),

    # Tool Alerts
    AlertRule(
        name="ToolHighFailureRate",
        expr='sum(rate(jebat_tool_invocations_total{status="error"}[5m])) by (tool) / sum(rate(jebat_tool_invocations_total[5m])) by (tool) > 0.1',
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "tools", "team": "platform"},
        annotations={
            "summary": "Tool {{ $labels.tool }} failure rate > 10%",
        },
    ),
    AlertRule(
        name="ToolHighLatency",
        expr='histogram_quantile(0.95, sum(rate(jebat_tool_duration_seconds_bucket[5m])) by (le, tool)) > 10',
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "tools", "team": "platform"},
        annotations={
            "summary": "Tool {{ $labels.tool }} p95 latency > 10s",
        },
    ),

    # Agent Alerts
    AlertRule(
        name="AgentStuck",
        expr='time() - jebat_agent_last_activity_timestamp_seconds > 600',
        severity=AlertSeverity.CRITICAL,
        for_duration="10m",
        labels={"component": "agents", "team": "platform"},
        annotations={
            "summary": "Agent {{ $labels.agent_id }} stuck for > 10 minutes",
        },
    ),

    # Memory Alerts
    AlertRule(
        name="MemoryHighPressure",
        expr='jebat_memory_usage_bytes / jebat_memory_limit_bytes > 0.85',
        severity=AlertSeverity.WARNING,
        for_duration="10m",
        labels={"component": "memory", "team": "platform"},
        annotations={
            "summary": "Memory layer {{ $labels.layer }} at {{ $value | humanizePercentage }} capacity",
        },
    ),
    AlertRule(
        name="MemoryConsolidationLag",
        expr='time() - jebat_memory_last_consolidation_timestamp_seconds > 3600',
        severity=AlertSeverity.WARNING,
        for_duration="1h",
        labels={"component": "memory", "team": "platform"},
        annotations={
            "summary": "Memory consolidation hasn't run in > 1 hour for {{ $labels.layer }}",
        },
    ),

    # MCP Alerts
    AlertRule(
        name="MCPHighLatency",
        expr='histogram_quantile(0.99, sum(rate(jebat_mcp_duration_seconds_bucket[5m])) by (le, method, transport)) > 10',
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "mcp", "team": "platform"},
        annotations={
            "summary": "MCP {{ $labels.method }} p99 latency > 10s",
        },
    ),
    AlertRule(
        name="MCPRequestFailures",
        expr='sum(rate(jebat_mcp_requests_total{status="error"}[5m])) by (method, transport) / sum(rate(jebat_mcp_requests_total[5m])) by (method, transport) > 0.02',
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "mcp", "team": "platform"},
        annotations={
            "summary": "MCP {{ $labels.method }} failure rate > 2%",
        },
    ),

    # System Alerts
    AlertRule(
        name="HighMemoryUsage",
        expr='jebat_memory_usage_bytes > 8e9',  # 8GB
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "system", "team": "platform"},
        annotations={
            "summary": "Process memory usage > 8GB",
        },
    ),
    AlertRule(
        name="HighCPUUsage",
        expr='rate(process_cpu_seconds_total[5m]) > 4',  # 4 cores
        severity=AlertSeverity.WARNING,
        for_duration="5m",
        labels={"component": "system", "team": "platform"},
        annotations={
            "summary": "Process CPU usage > 400% (4 cores)",
        },
    ),
]