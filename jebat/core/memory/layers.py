"""Memory layers for the 5-tier memory system."""

from __future__ import annotations

from enum import Enum


class MemoryLayer(str, Enum):
    M0_SENSORY = "M0"
    M1_EPISODIC = "M1"
    M2_SEMANTIC = "M2"
    M3_CONCEPTUAL = "M3"
    M4_PERMANENT = "M4"
