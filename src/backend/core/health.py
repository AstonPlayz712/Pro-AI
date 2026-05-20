"""Source health state machine.

Implements §1.7 HealthState (UNKNOWN | HEALTHY | DEGRADED | UNREACHABLE |
REVOKED | DISABLED) and the transition rules that gate outbound calls.
"""
from __future__ import annotations

from enum import Enum
from threading import RLock
from typing import Callable, Dict, List, Tuple


class HealthState(str, Enum):
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNREACHABLE = "UNREACHABLE"
    REVOKED = "REVOKED"
    DISABLED = "DISABLED"


_ALLOWED_TRANSITIONS: Dict[HealthState, List[HealthState]] = {
    HealthState.UNKNOWN: [
        HealthState.HEALTHY,
        HealthState.DEGRADED,
        HealthState.UNREACHABLE,
        HealthState.DISABLED,
        HealthState.REVOKED,
    ],
    HealthState.HEALTHY: [
        HealthState.DEGRADED,
        HealthState.UNREACHABLE,
        HealthState.DISABLED,
        HealthState.REVOKED,
    ],
    HealthState.DEGRADED: [
        HealthState.HEALTHY,
        HealthState.UNREACHABLE,
        HealthState.DISABLED,
        HealthState.REVOKED,
    ],
    HealthState.UNREACHABLE: [
        HealthState.HEALTHY,
        HealthState.DEGRADED,
        HealthState.DISABLED,
        HealthState.REVOKED,
    ],
    HealthState.DISABLED: [
        HealthState.UNKNOWN,
        HealthState.HEALTHY,
    ],
    HealthState.REVOKED: [
        HealthState.UNKNOWN,
        HealthState.DISABLED,
    ],
}

CALLABLE_STATES = {HealthState.HEALTHY, HealthState.DEGRADED}
WARNING_STATES = {HealthState.DEGRADED}


def is_valid_transition(current: HealthState, target: HealthState) -> bool:
    if current == target:
        return True
    return target in _ALLOWED_TRANSITIONS.get(current, [])


HealthListener = Callable[[str, HealthState, HealthState], None]
"""Receives (source_id, old_state, new_state) on every transition."""


class HealthMonitor:
    """Tracks source health and fires listeners on transitions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._state: Dict[str, HealthState] = {}
        self._consecutive_timeouts: Dict[str, int] = {}
        self._listeners: List[HealthListener] = []

    def add_listener(self, listener: HealthListener) -> None:
        with self._lock:
            self._listeners.append(listener)

    def state(self, source_id: str) -> HealthState:
        with self._lock:
            return self._state.get(source_id, HealthState.UNKNOWN)

    def set(self, source_id: str, target: HealthState) -> Tuple[HealthState, HealthState]:
        with self._lock:
            old = self._state.get(source_id, HealthState.UNKNOWN)
            if not is_valid_transition(old, target):
                return (old, old)
            self._state[source_id] = target
            if target != old:
                self._emit(source_id, old, target)
            return (old, target)

    def record_ok(self, source_id: str) -> None:
        with self._lock:
            self._consecutive_timeouts[source_id] = 0
            old = self._state.get(source_id, HealthState.UNKNOWN)
            if old in (HealthState.REVOKED, HealthState.DISABLED):
                return
            if old != HealthState.HEALTHY:
                self._transition(source_id, old, HealthState.HEALTHY)

    def record_degraded(self, source_id: str, reason: str = "latency_spike") -> None:
        with self._lock:
            old = self._state.get(source_id, HealthState.UNKNOWN)
            if old in (HealthState.REVOKED, HealthState.DISABLED, HealthState.UNREACHABLE):
                return
            if old != HealthState.DEGRADED:
                self._transition(source_id, old, HealthState.DEGRADED)

    def record_timeout(self, source_id: str) -> None:
        with self._lock:
            count = self._consecutive_timeouts.get(source_id, 0) + 1
            self._consecutive_timeouts[source_id] = count
            old = self._state.get(source_id, HealthState.UNKNOWN)
            if count >= 3:
                if old not in (HealthState.REVOKED, HealthState.DISABLED):
                    self._transition(source_id, old, HealthState.UNREACHABLE)
            else:
                if old in (HealthState.HEALTHY, HealthState.UNKNOWN):
                    self._transition(source_id, old, HealthState.DEGRADED)

    def record_auth_failure(self, source_id: str) -> None:
        with self._lock:
            old = self._state.get(source_id, HealthState.UNKNOWN)
            self._transition(source_id, old, HealthState.REVOKED)

    def record_admin_disable(self, source_id: str) -> None:
        with self._lock:
            old = self._state.get(source_id, HealthState.UNKNOWN)
            self._transition(source_id, old, HealthState.DISABLED)

    def record_admin_reenable(self, source_id: str) -> None:
        with self._lock:
            old = self._state.get(source_id, HealthState.UNKNOWN)
            if old in (HealthState.DISABLED, HealthState.REVOKED):
                self._transition(source_id, old, HealthState.UNKNOWN)

    def _transition(self, source_id: str, old: HealthState, new: HealthState) -> None:
        if not is_valid_transition(old, new):
            return
        self._state[source_id] = new
        if old != new:
            self._emit(source_id, old, new)

    def _emit(self, source_id: str, old: HealthState, new: HealthState) -> None:
        for listener in list(self._listeners):
            try:
                listener(source_id, old, new)
            except Exception:
                pass
