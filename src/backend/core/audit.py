"""Append-only decision log.

Implements §1.11 (Decision log). Every permission decision, outbound call,
and state transition that affects DAI's privileges is recorded. The log is
session-scoped and append-only; entries are never mutated or deleted.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DecisionKind(str, Enum):
    PERMISSION_CHECK = "permission_check"
    OUTBOUND_CALL = "outbound_call"
    HEALTH_TRANSITION = "health_transition"
    SCOPE_CHANGE = "scope_change"
    VAULT_ACTION = "vault_action"
    SESSION_TRANSITION = "session_transition"
    QUOTA_LEASE = "quota_lease"
    MODE_TRANSITION = "mode_transition"
    GOAL_TRANSITION = "goal_transition"
    SUBTASK_TRANSITION = "subtask_transition"


class DecisionLogEntry(BaseModel):
    """Single entry in the append-only decision log."""

    entry_id: str = Field(default_factory=lambda: f"dlg_{uuid.uuid4().hex[:12]}")
    session_id: Optional[str] = None
    kind: DecisionKind
    actor: str  # "dai" | "al" | "admin" | "system"
    source_id: Optional[str] = None
    action: Optional[str] = None
    allowed: Optional[bool] = None
    reasons: List[str] = Field(default_factory=list)
    rule_chain: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditLog:
    """In-memory append-only decision log."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: List[DecisionLogEntry] = []

    def record(self, entry: DecisionLogEntry) -> DecisionLogEntry:
        with self._lock:
            self._entries.append(entry)
            return entry

    def log(
        self,
        kind: DecisionKind,
        *,
        actor: str,
        session_id: Optional[str] = None,
        source_id: Optional[str] = None,
        action: Optional[str] = None,
        allowed: Optional[bool] = None,
        reasons: Optional[List[str]] = None,
        rule_chain: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> DecisionLogEntry:
        entry = DecisionLogEntry(
            kind=kind,
            actor=actor,
            session_id=session_id,
            source_id=source_id,
            action=action,
            allowed=allowed,
            reasons=list(reasons or []),
            rule_chain=list(rule_chain or []),
            details=dict(details or {}),
        )
        return self.record(entry)

    def list(
        self,
        *,
        session_id: Optional[str] = None,
        kind: Optional[DecisionKind] = None,
        limit: Optional[int] = None,
    ) -> List[DecisionLogEntry]:
        with self._lock:
            entries = list(self._entries)
            if session_id is not None:
                entries = [e for e in entries if e.session_id == session_id]
            if kind is not None:
                entries = [e for e in entries if e.kind == kind]
            if limit is not None:
                entries = entries[-limit:]
            return entries

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)
