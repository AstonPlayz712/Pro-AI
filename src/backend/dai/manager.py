"""DAIManager — per-session reasoning state.

Spec references:
  §7 DAI state model
  §8 DAI endpoints
  §9 Mode transitions (with AL veto)
"""
from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Dict, Optional

from ..al.manager import ALManager
from ..core.audit import DecisionKind
from ..core.context import ChipOrigin
from ..core.errors import AutoException, make_error
from .models import (
    DAIMode,
    DAIState,
    DAIStateProjection,
    Goal,
    GoalDraftRequest,
    GoalState,
    GoalTransitionRequest,
    MessageRequest,
    MessageResponse,
    Subtask,
    SubtaskDraftRequest,
    SubtaskState,
    SubtaskTransitionRequest,
    TimelineEvent,
    goal_transition_allowed,
    subtask_transition_allowed,
)


_MODE_TRANSITIONS: Dict[DAIMode, list] = {
    DAIMode.ANALYST: [DAIMode.ARCHITECT, DAIMode.DEBUGGER, DAIMode.BUILDER],
    DAIMode.ARCHITECT: [DAIMode.ANALYST, DAIMode.BUILDER, DAIMode.DEBUGGER],
    DAIMode.DEBUGGER: [DAIMode.ANALYST, DAIMode.ARCHITECT, DAIMode.BUILDER],
    DAIMode.BUILDER: [DAIMode.ANALYST, DAIMode.ARCHITECT, DAIMode.DEBUGGER],
}


_INTENT_TO_MODE = {
    "question": DAIMode.ANALYST,
    "analyse": DAIMode.ANALYST,
    "build": DAIMode.BUILDER,
    "debug": DAIMode.DEBUGGER,
    "design": DAIMode.ARCHITECT,
}


class _SessionSlot:
    """Holds all DAI state for one session."""

    __slots__ = ("state", "goals", "subtasks", "timeline")

    def __init__(self, session_id: str) -> None:
        self.state = DAIState(session_id=session_id)
        self.goals: Dict[str, Goal] = {}
        self.subtasks: Dict[str, Subtask] = {}
        self.timeline: list = []


class DAIManager:
    """Runs DAI's reasoning state machines on top of an ALManager."""

    def __init__(self, al: ALManager) -> None:
        self._al = al
        self._lock = RLock()
        self._slots: Dict[str, _SessionSlot] = {}

    def _slot(self, session_id: str) -> _SessionSlot:
        self._al.sessions.get(session_id)
        with self._lock:
            slot = self._slots.get(session_id)
            if slot is None:
                slot = _SessionSlot(session_id)
                self._slots[session_id] = slot
            return slot

    def _emit_event(
        self,
        slot: _SessionSlot,
        *,
        kind: str,
        summary: str,
        details: Optional[Dict] = None,
    ) -> TimelineEvent:
        evt = TimelineEvent(
            session_id=slot.state.session_id,
            kind=kind,
            summary=summary,
            details=dict(details or {}),
        )
        slot.timeline.append(evt)
        return evt

    def project(self, session_id: str) -> DAIStateProjection:
        slot = self._slot(session_id)
        active_goal = None
        if slot.state.active_goal_id is not None:
            active_goal = slot.goals.get(slot.state.active_goal_id)
        return DAIStateProjection(
            session_id=session_id,
            mode=slot.state.mode,
            confidence=slot.state.confidence,
            active_goal=active_goal,
            goals=list(slot.goals.values()),
            subtasks=list(slot.subtasks.values()),
            timeline=list(slot.timeline[-100:]),
            locked=slot.state.locked,
            locked_reason=slot.state.locked_reason,
        )

    # -- Mode transitions (§9) -------------------------------------------

    def set_mode(self, session_id: str, target: DAIMode, *, reason: str = "") -> DAIStateProjection:
        slot = self._slot(session_id)
        if slot.state.locked:
            raise make_error(
                "ErrDAIStateLocked",
                f"DAI state locked: {slot.state.locked_reason or 'unknown'}",
            )
        current = slot.state.mode
        if target != current and target not in _MODE_TRANSITIONS.get(current, []):
            raise make_error(
                "ErrModeVetoed",
                f"Mode transition {current.value}→{target.value} is not allowed",
            )
        if target == DAIMode.BUILDER:
            if slot.state.active_goal_id is None:
                raise make_error(
                    "ErrModeVetoed",
                    "Cannot enter BUILDER mode without an active goal",
                )
        if target == DAIMode.DEBUGGER and not reason:
            has_failed = any(s.state == SubtaskState.FAILED for s in slot.subtasks.values())
            if not has_failed:
                raise make_error(
                    "ErrModeVetoed",
                    "DEBUGGER requires a failed subtask or an explicit reason",
                )
        old = current
        slot.state.mode = target
        self._emit_event(
            slot,
            kind="mode",
            summary=f"mode {old.value} → {target.value}",
            details={"reason": reason} if reason else {},
        )
        self._al.audit.log(
            DecisionKind.MODE_TRANSITION,
            actor="dai",
            session_id=session_id,
            details={"old": old.value, "new": target.value, "reason": reason},
        )
        return self.project(session_id)

    # -- Goals (§7.2) ----------------------------------------------------

    def draft_goal(self, session_id: str, req: GoalDraftRequest) -> Goal:
        slot = self._slot(session_id)
        if req.parent_goal_id is not None and req.parent_goal_id not in slot.goals:
            raise make_error(
                "ErrGoalConflict",
                f"Parent goal {req.parent_goal_id} does not exist",
            )
        goal = Goal(
            session_id=session_id,
            title=req.title,
            description=req.description,
            parent_goal_id=req.parent_goal_id,
        )
        slot.goals[goal.goal_id] = goal
        self._emit_event(
            slot,
            kind="goal",
            summary=f"goal drafted: {goal.title}",
            details={"goal_id": goal.goal_id},
        )
        self._al.audit.log(
            DecisionKind.GOAL_TRANSITION,
            actor="dai",
            session_id=session_id,
            details={"goal_id": goal.goal_id, "new": GoalState.DRAFT.value, "title": goal.title},
        )
        if req.activate:
            self.transition_goal(
                session_id,
                GoalTransitionRequest(goal_id=goal.goal_id, target_state=GoalState.ACTIVE),
            )
            goal = slot.goals[goal.goal_id]
        return goal

    def transition_goal(self, session_id: str, req: GoalTransitionRequest) -> Goal:
        slot = self._slot(session_id)
        goal = slot.goals.get(req.goal_id)
        if goal is None:
            raise make_error("ErrGoalConflict", f"Unknown goal: {req.goal_id}")
        if not goal_transition_allowed(goal.state, req.target_state):
            raise make_error(
                "ErrGoalConflict",
                f"Goal {goal.goal_id}: {goal.state.value} → {req.target_state.value} is not allowed",
            )
        if req.target_state == GoalState.ACTIVE:
            for other_id, other in slot.goals.items():
                if other_id == goal.goal_id:
                    continue
                if other.state == GoalState.ACTIVE:
                    raise make_error(
                        "ErrGoalConflict",
                        f"Another active goal exists: {other.goal_id}",
                    )
        old = goal.state
        goal.state = req.target_state
        goal.updated_at = datetime.now(timezone.utc)
        if req.target_state == GoalState.BLOCKED and req.reason:
            goal.blocker_reasons.append(req.reason)
        if req.target_state == GoalState.ACTIVE:
            slot.state.active_goal_id = goal.goal_id
        elif goal.goal_id == slot.state.active_goal_id and req.target_state in (
            GoalState.ACHIEVED,
            GoalState.ABANDONED,
        ):
            slot.state.active_goal_id = None
        self._emit_event(
            slot,
            kind="goal",
            summary=f"goal {goal.goal_id}: {old.value} → {req.target_state.value}",
            details={"reason": req.reason} if req.reason else {},
        )
        self._al.audit.log(
            DecisionKind.GOAL_TRANSITION,
            actor="dai",
            session_id=session_id,
            details={
                "goal_id": goal.goal_id,
                "old": old.value,
                "new": req.target_state.value,
                "reason": req.reason or "",
            },
        )
        return goal

    # -- Subtasks (§7.3) -------------------------------------------------

    def draft_subtask(self, session_id: str, req: SubtaskDraftRequest) -> Subtask:
        slot = self._slot(session_id)
        goal = slot.goals.get(req.goal_id)
        if goal is None:
            raise make_error("ErrGoalConflict", f"Unknown goal: {req.goal_id}")
        if goal.state not in (GoalState.DRAFT, GoalState.ACTIVE, GoalState.BLOCKED):
            raise make_error(
                "ErrGoalConflict",
                f"Goal {goal.goal_id} is {goal.state.value}; cannot attach subtasks",
            )
        for dep in req.depends_on:
            if dep not in slot.subtasks:
                raise make_error("ErrSubtaskUnknown", f"Unknown dependency: {dep}")
            if self._would_create_cycle(slot, depends_on=dep, new_ancestor_set=set(req.depends_on)):
                raise make_error(
                    "ErrSubtaskCycle",
                    f"Adding dependency on {dep} would create a cycle",
                )
        sub = Subtask(
            session_id=session_id,
            goal_id=goal.goal_id,
            title=req.title,
            description=req.description,
            depends_on=list(req.depends_on),
            target_source_id=req.target_source_id,
            target_capability=req.target_capability,
        )
        slot.subtasks[sub.subtask_id] = sub
        self._emit_event(
            slot,
            kind="subtask",
            summary=f"subtask queued: {sub.title}",
            details={"subtask_id": sub.subtask_id, "goal_id": sub.goal_id},
        )
        self._al.audit.log(
            DecisionKind.SUBTASK_TRANSITION,
            actor="dai",
            session_id=session_id,
            details={
                "subtask_id": sub.subtask_id,
                "new": SubtaskState.QUEUED.value,
                "goal_id": sub.goal_id,
            },
        )
        return sub

    def transition_subtask(self, session_id: str, req: SubtaskTransitionRequest) -> Subtask:
        slot = self._slot(session_id)
        sub = slot.subtasks.get(req.subtask_id)
        if sub is None:
            raise make_error("ErrSubtaskUnknown", f"Unknown subtask: {req.subtask_id}")
        if not subtask_transition_allowed(sub.state, req.target_state):
            raise make_error(
                "ErrSubtaskUnknown",
                f"Subtask {sub.subtask_id}: {sub.state.value} → {req.target_state.value} is not allowed",
            )
        if sub.state == SubtaskState.QUEUED and req.target_state == SubtaskState.RUNNING:
            for dep_id in sub.depends_on:
                dep = slot.subtasks.get(dep_id)
                if dep is None or dep.state != SubtaskState.DONE:
                    raise make_error(
                        "ErrSubtaskUnknown",
                        f"Dependency {dep_id} is not DONE; cannot run {sub.subtask_id}",
                    )
        old = sub.state
        sub.state = req.target_state
        sub.updated_at = datetime.now(timezone.utc)
        if req.target_state == SubtaskState.RUNNING:
            sub.attempts += 1
        if req.last_error is not None:
            sub.last_error = req.last_error
        if req.last_request_id is not None:
            sub.last_request_id = req.last_request_id
        self._emit_event(
            slot,
            kind="subtask",
            summary=f"subtask {sub.subtask_id}: {old.value} → {req.target_state.value}",
            details={"last_error": sub.last_error} if sub.last_error else {},
        )
        self._al.audit.log(
            DecisionKind.SUBTASK_TRANSITION,
            actor="dai",
            session_id=session_id,
            details={
                "subtask_id": sub.subtask_id,
                "old": old.value,
                "new": req.target_state.value,
            },
        )
        active_id = slot.state.active_goal_id
        if active_id is not None and req.target_state == SubtaskState.DONE:
            active_subs = [s for s in slot.subtasks.values() if s.goal_id == active_id]
            if active_subs and all(s.state == SubtaskState.DONE for s in active_subs):
                self.transition_goal(
                    session_id,
                    GoalTransitionRequest(goal_id=active_id, target_state=GoalState.ACHIEVED),
                )
        return sub

    def _would_create_cycle(
        self, slot: _SessionSlot, *, depends_on: str, new_ancestor_set: set
    ) -> bool:
        seen = set()
        stack = [depends_on]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            if cur in new_ancestor_set and cur != depends_on:
                return True
            node = slot.subtasks.get(cur)
            if node is None:
                continue
            stack.extend(node.depends_on)
        return False

    # -- Message handling (§8.1) ----------------------------------------

    def handle_message(self, session_id: str, req: MessageRequest) -> MessageResponse:
        slot = self._slot(session_id)
        if slot.state.locked:
            raise make_error(
                "ErrDAIStateLocked",
                f"DAI is locked: {slot.state.locked_reason or 'unknown'}",
            )
        if req.intent and req.intent in _INTENT_TO_MODE:
            suggested = _INTENT_TO_MODE[req.intent]
            if suggested != slot.state.mode:
                if suggested == DAIMode.BUILDER and slot.state.active_goal_id is None:
                    self.draft_goal(
                        session_id,
                        GoalDraftRequest(
                            title=req.content[:80] or "build task",
                            description=req.content,
                            activate=True,
                        ),
                    )
                try:
                    self.set_mode(session_id, suggested, reason=f"intent={req.intent}")
                except AutoException:
                    pass
        evt = self._emit_event(
            slot,
            kind="message",
            summary=f"user: {req.content[:120]}",
            details={"intent": req.intent, "attachments": len(req.attachments)},
        )
        self._al.fabric.add_chip(
            session_id=session_id,
            topic="conversation",
            payload={"content": req.content, "intent": req.intent or "unspecified"},
            origin=ChipOrigin.DAI,
            pinned=False,
            ttl_sec=600,
        )
        reply = self._compose_reply(slot, req)
        return MessageResponse(
            session_id=session_id,
            mode=slot.state.mode,
            reply=reply,
            goal_id=slot.state.active_goal_id,
            subtask_ids=[
                s.subtask_id
                for s in slot.subtasks.values()
                if s.goal_id == slot.state.active_goal_id and s.state == SubtaskState.QUEUED
            ],
            timeline_event_id=evt.event_id,
        )

    def _compose_reply(self, slot: _SessionSlot, req: MessageRequest) -> str:
        """Deterministic, spec-faithful reply. No external LLM — DAI's outputs
        here summarise its own state so the DAI↔AL contract is exercisable
        end-to-end without any model call."""
        mode = slot.state.mode.value
        goal = None
        if slot.state.active_goal_id:
            goal = slot.goals.get(slot.state.active_goal_id)
        parts = [f"[{mode}]"]
        if goal is not None:
            parts.append(f"goal={goal.title}")
        parts.append(f"ack: {req.content[:120]}")
        return " | ".join(parts)

    def context_map(self, session_id: str) -> Dict:
        self._slot(session_id)
        return self._al.context_map(session_id)
