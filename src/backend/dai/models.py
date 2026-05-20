"""DAI internal state + API models.

Spec references:
  §7.1 Mode (Architect | Debugger | Analyst | Builder)
  §7.2 Goal state machine
  §7.3 Subtask state machine
  §7.4 Timeline
  §8 DAI endpoints
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DAIMode(str, Enum):
    ARCHITECT = "architect"
    DEBUGGER = "debugger"
    ANALYST = "analyst"
    BUILDER = "builder"


class GoalState(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    BLOCKED = "blocked"
    ACHIEVED = "achieved"
    ABANDONED = "abandoned"


class SubtaskState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_ON_AL = "waiting_on_al"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


_GOAL_TRANSITIONS: Dict[GoalState, List[GoalState]] = {
    GoalState.DRAFT: [GoalState.ACTIVE, GoalState.ABANDONED],
    GoalState.ACTIVE: [GoalState.BLOCKED, GoalState.ACHIEVED, GoalState.ABANDONED],
    GoalState.BLOCKED: [GoalState.ACTIVE, GoalState.ABANDONED],
    GoalState.ACHIEVED: [],
    GoalState.ABANDONED: [],
}

_SUBTASK_TRANSITIONS: Dict[SubtaskState, List[SubtaskState]] = {
    SubtaskState.QUEUED: [SubtaskState.RUNNING, SubtaskState.CANCELLED],
    SubtaskState.RUNNING: [
        SubtaskState.WAITING_ON_AL,
        SubtaskState.DONE,
        SubtaskState.FAILED,
        SubtaskState.CANCELLED,
    ],
    SubtaskState.WAITING_ON_AL: [
        SubtaskState.RUNNING,
        SubtaskState.FAILED,
        SubtaskState.CANCELLED,
    ],
    SubtaskState.DONE: [],
    SubtaskState.FAILED: [SubtaskState.QUEUED],
    SubtaskState.CANCELLED: [],
}


def goal_transition_allowed(cur: GoalState, target: GoalState) -> bool:
    return cur == target or target in _GOAL_TRANSITIONS.get(cur, [])


def subtask_transition_allowed(cur: SubtaskState, target: SubtaskState) -> bool:
    return cur == target or target in _SUBTASK_TRANSITIONS.get(cur, [])


class ChipRef(BaseModel):
    chip_id: str
    topic: str


class Goal(BaseModel):
    goal_id: str = Field(default_factory=lambda: f"gol_{uuid.uuid4().hex[:12]}")
    session_id: str
    title: str
    description: str = ""
    state: GoalState = GoalState.DRAFT
    parent_goal_id: Optional[str] = None
    blocker_reasons: List[str] = Field(default_factory=list)
    chip_refs: List[ChipRef] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Subtask(BaseModel):
    subtask_id: str = Field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:12]}")
    session_id: str
    goal_id: str
    title: str
    description: str = ""
    state: SubtaskState = SubtaskState.QUEUED
    depends_on: List[str] = Field(default_factory=list)
    target_source_id: Optional[str] = None
    target_capability: Optional[str] = None
    attempts: int = 0
    last_error: Optional[str] = None
    last_request_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TimelineEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    session_id: str
    kind: str
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DAIState(BaseModel):
    """Per-session DAI state (§7)."""

    session_id: str
    mode: DAIMode = DAIMode.ANALYST
    confidence: float = 0.5
    active_goal_id: Optional[str] = None
    locked: bool = False
    locked_reason: Optional[str] = None


class DAIStateProjection(BaseModel):
    """DAI-visible projection returned by /dai/state (§8.2)."""

    session_id: str
    mode: DAIMode
    confidence: float
    active_goal: Optional[Goal]
    goals: List[Goal]
    subtasks: List[Subtask]
    timeline: List[TimelineEvent]
    locked: bool
    locked_reason: Optional[str]


class MessageRequest(BaseModel):
    """Inbound user → DAI message (§8.1)."""

    content: str
    intent: Optional[str] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)


class MessageResponse(BaseModel):
    session_id: str
    mode: DAIMode
    reply: str
    goal_id: Optional[str] = None
    subtask_ids: List[str] = Field(default_factory=list)
    timeline_event_id: str


class GoalDraftRequest(BaseModel):
    title: str
    description: str = ""
    parent_goal_id: Optional[str] = None
    activate: bool = True


class GoalTransitionRequest(BaseModel):
    goal_id: str
    target_state: GoalState
    reason: Optional[str] = None


class SubtaskDraftRequest(BaseModel):
    goal_id: str
    title: str
    description: str = ""
    depends_on: List[str] = Field(default_factory=list)
    target_source_id: Optional[str] = None
    target_capability: Optional[str] = None


class SubtaskTransitionRequest(BaseModel):
    subtask_id: str
    target_state: SubtaskState
    last_error: Optional[str] = None
    last_request_id: Optional[str] = None
