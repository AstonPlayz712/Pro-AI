"""
DAI state projection.

DAIProjection is the canonical snapshot of DirectorAI's internal state
that may be serialised and sent to the frontend.  It is defined as a
dataclass for strong typing while providing a helper that produces a
plain, JSON-serialisable dict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Nested structures
# ---------------------------------------------------------------------------

@dataclass
class Goal:
    id: str
    description: str
    success_criteria: List[str] = field(default_factory=list)


@dataclass
class Subtask:
    id: str
    description: str
    status: str          # e.g. "pending" | "in_progress" | "done" | "failed"
    confidence: float    # 0.0 – 1.0


@dataclass
class TimelineEvent:
    timestamp: float     # Unix epoch (seconds)
    event_type: str      # e.g. "goal_update" | "subtask_transition" | "al_interaction"
    details: str


@dataclass
class ChipRef:
    """Lightweight reference to a context chip — payload is never copied."""
    chip_id: str
    source: str
    confidence: float    # 0.0 – 1.0
    ttl: float           # Unix epoch expiry; 0 means no expiry
    pinned: bool = False


@dataclass
class HealthStatus:
    chip_conflicts: bool = False
    expired_chips: List[str] = field(default_factory=list)
    low_confidence: bool = False


# ---------------------------------------------------------------------------
# Top-level projection
# ---------------------------------------------------------------------------

@dataclass
class DAIProjection:
    """
    Immutable snapshot of the current DAI session state.

    Parameters are intentionally optional so a projection can be built
    incrementally before all fields are populated.
    """

    goal: Optional[Goal] = None
    subtasks: List[Subtask] = field(default_factory=list)
    timeline: List[TimelineEvent] = field(default_factory=list)
    chips: List[ChipRef] = field(default_factory=list)
    mode: str = "architect"
    tone: str = "precise"
    health: HealthStatus = field(default_factory=HealthStatus)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dict for the frontend."""
        return {
            "goal": (
                {
                    "id": self.goal.id,
                    "description": self.goal.description,
                    "success_criteria": self.goal.success_criteria,
                }
                if self.goal is not None
                else None
            ),
            "subtasks": [
                {
                    "id": s.id,
                    "description": s.description,
                    "status": s.status,
                    "confidence": s.confidence,
                }
                for s in self.subtasks
            ],
            "timeline": [
                {
                    "timestamp": e.timestamp,
                    "event_type": e.event_type,
                    "details": e.details,
                }
                for e in self.timeline
            ],
            "chips": [
                {
                    "chip_id": c.chip_id,
                    "source": c.source,
                    "confidence": c.confidence,
                    "ttl": c.ttl,
                    "pinned": c.pinned,
                }
                for c in self.chips
            ],
            "mode": self.mode,
            "tone": self.tone,
            "health": {
                "chip_conflicts": self.health.chip_conflicts,
                "expired_chips": self.health.expired_chips,
                "low_confidence": self.health.low_confidence,
            },
        }


__all__ = [
    "Goal",
    "Subtask",
    "TimelineEvent",
    "ChipRef",
    "HealthStatus",
    "DAIProjection",
]
