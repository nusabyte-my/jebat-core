"""
JEBAT Memory Layers

5-layer memory architecture inspired by human cognition.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryLayer(str, Enum):
    """Memory layer types."""

    M0_SENSORY = "m0_sensory"
    M1_EPISODIC = "m1_episodic"
    M2_SEMANTIC = "m2_semantic"
    M3_CONCEPTUAL = "m3_conceptual"
    M4_PROCEDURAL = "m4_procedural"


class MemoryModality(str, Enum):
    """Types of memory content."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"
    STRUCTURED = "structured"


class MemoryImportance(str, Enum):
    """Memory importance levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRIVIAL = "trivial"


@dataclass
class HeatScore:
    """
    Memory importance heat score.

    Calculated from:
    - Visit frequency (30%)
    - Interaction depth (25%)
    - Recency (25%)
    - Cross-references (15%)
    - Explicit rating (5%)
    """

    visit_frequency: float = 0.0
    interaction_depth: float = 0.0
    recency: float = 1.0
    cross_reference_count: float = 0.0
    explicit_rating: float = 0.5

    WEIGHT_FREQUENCY = 0.30
    WEIGHT_DEPTH = 0.25
    WEIGHT_RECENCY = 0.25
    WEIGHT_CROSS_REF = 0.15
    WEIGHT_EXPLICIT = 0.05

    def calculate(self) -> float:
        """Calculate total heat score (0-1)."""
        return (
            self.WEIGHT_FREQUENCY * self.visit_frequency
            + self.WEIGHT_DEPTH * self.interaction_depth
            + self.WEIGHT_RECENCY * self.recency
            + self.WEIGHT_CROSS_REF * self.cross_reference_count
            + self.WEIGHT_EXPLICIT * self.explicit_rating
        )


@dataclass
class MemoryMetadata:
    """Memory metadata."""

    user_id: str
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    modality: MemoryModality = MemoryModality.TEXT
    importance: MemoryImportance = MemoryImportance.MEDIUM
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Memory:
    """
    Memory representation.

    Attributes:
        memory_id: Unique identifier
        content: Memory content
        layer: Memory layer
        metadata: Memory metadata
        heat: Heat score
        created_at: Creation timestamp
        updated_at: Last update timestamp
        expires_at: Optional expiration
    """

    memory_id: str
    content: str
    layer: MemoryLayer
    metadata: MemoryMetadata
    heat: HeatScore
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "layer": self.layer.value,
            "metadata": {
                "user_id": self.metadata.user_id,
                "tags": self.metadata.tags,
                "modality": self.metadata.modality.value,
            },
            "heat": self.heat.calculate(),
            "created_at": self.created_at.isoformat(),
        }
