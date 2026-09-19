from .self_learning import (
    Strategy,
    LearningGoal,
    LearningExperience,
    PerformanceMetric,
    MetaLearner,
    AlertRule,
    Alert,
    AlertSeverity,
    AlertManager,
    WebhookNotifier,
    SlackNotifier,
    PagerDutyNotifier,
    DEFAULT_ALERT_RULES,
)

# Memory classes are defined in jebat.features.memory (the canonical
# implementation). This package used to carry a byte-for-byte fork in
# `.memory` that shadowed it: two distinct EnhancedMemorySystem classes with
# two independent class hierarchies for the same store. The fork had no
# symbols of its own, was imported by nothing, and had drifted — it still
# carried the unreachable-0.8 pattern predicate, the strength-ratcheting
# decay(), and the empty-concept generalization bug that were fixed in the
# canonical module. Re-exported here so existing import paths keep working.
from ..memory import (
    EnhancedMemorySystem,
    MemoryType,
    MemoryPhase,
    MemoryTrace,
    MemoryQuery,
    ConsolidationResult,
    WorkingMemory,
    SemanticMemory,
    ProceduralMemory,
    SelfLearningMemory,
)

from .mimpi import (
    DreamType,
    DreamPhase,
    DreamIntensity,
    DreamScene,
    Dream,
    DreamEngine,
    DreamScheduler,
    quick_dream,
    creative_brainstorm,
    adversarial_dream,
    planning_dream,
)

from ..code_agent.enhanced_agent import (
    EnhancedCodeAgent as SelfLearningAgent,
    LoopConfig,
    LoopExitCondition,
    OrchestrationMode,
    AgentBranchStrategy,
    AgentSpec,
    OrchestrationPlan,
    CostTracker,
    SpecManager,
    SkillMarketplace,
    AgentMemory,
    BranchAgentManager,
    create_enhanced_agent,
    create_orchestration_plan,
)

# Convenience alias so callers can use a single consistent entrypoint.
create_self_learning_agent = create_enhanced_agent

__all__ = [
    # SelfLearningAgent (alias for EnhancedCodeAgent)
    "SelfLearningAgent",
    "create_self_learning_agent",
    "Strategy",
    "LearningGoal",
    "LearningExperience",
    "PerformanceMetric",
    "MetaLearner",
    "AlertRule",
    "Alert",
    "AlertSeverity",
    "AlertManager",
    "WebhookNotifier",
    "SlackNotifier",
    "PagerDutyNotifier",
    "DEFAULT_ALERT_RULES",

    # Memory
    "EnhancedMemorySystem",
    "MemoryType",
    "MemoryPhase",
    "MemoryTrace",
    "MemoryQuery",
    "ConsolidationResult",
    "WorkingMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "SelfLearningMemory",

    # Mimpi (Dreams)
    "DreamType",
    "DreamPhase",
    "DreamIntensity",
    "DreamScene",
    "Dream",
    "DreamEngine",
    "DreamScheduler",
    "quick_dream",
    "creative_brainstorm",
    "adversarial_dream",
    "planning_dream",

    # Enhanced Agent
    "EnhancedCodeAgent",
    "LoopConfig",
    "LoopExitCondition",
    "OrchestrationMode",
    "AgentBranchStrategy",
    "AgentSpec",
    "OrchestrationPlan",
    "CostTracker",
    "SpecManager",
    "SkillMarketplace",
    "AgentMemory",
    "BranchAgentManager",
    "create_enhanced_agent",
    "create_orchestration_plan",
]