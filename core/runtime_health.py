"""Runtime health tracking.

Tracks:
- engine health
- task failures
- event loop stalls (placeholder)
- capability errors

Emits health events and writes transcript entries when available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from core.debug_log import debug_log
from core.event_bus import EventBus
from core.session_transcript import SessionTranscript


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class RuntimeHealth:
    """Mutable health tracker."""

    bus: EventBus
    transcript: SessionTranscript

    engine_status: dict[str, str] = field(default_factory=dict)
    task_failures: int = 0
    capability_errors: int = 0
    last_loop_tick: Optional[datetime] = None

    def tick_loop(self) -> None:
        self.last_loop_tick = utc_now()

    def set_engine_health(self, engine: str, status: str, *, detail: str = "") -> None:
        self.engine_status[engine] = status
        debug_log(
            "Engine health updated",
            component="runtime_health",
            data={"engine": engine, "status": status, "detail": detail},
        )
        self.bus.emit(
            "health.engine",
            {"engine": engine, "status": status, "detail": detail},
            source="runtime_health",
        )
        self.transcript.append("health", f"Engine {engine}={status}", {"engine": engine, "status": status, "detail": detail})

    def record_task_failure(self, *, task_id: str, name: str, error: str) -> None:
        self.task_failures += 1
        debug_log(
            "Task failure recorded",
            component="runtime_health",
            level="WARN",
            data={"task_id": task_id, "name": name, "error": error, "count": self.task_failures},
        )
        self.bus.emit(
            "health.task_failure",
            {"task_id": task_id, "name": name, "error": error, "count": self.task_failures},
            source="runtime_health",
        )
        self.transcript.append("error", "Task failure", {"task_id": task_id, "name": name, "error": error})

    def record_capability_error(self, *, capability: str, error: str) -> None:
        self.capability_errors += 1
        debug_log(
            "Capability error recorded",
            component="runtime_health",
            level="WARN",
            data={"capability": capability, "error": error, "count": self.capability_errors},
        )
        self.bus.emit(
            "health.capability_error",
            {"capability": capability, "error": error, "count": self.capability_errors},
            source="runtime_health",
        )
        self.transcript.append("error", "Capability error", {"capability": capability, "error": error})

    def snapshot(self) -> dict[str, Any]:
        return {
            "engine_status": dict(self.engine_status),
            "task_failures": self.task_failures,
            "capability_errors": self.capability_errors,
            "last_loop_tick": self.last_loop_tick.isoformat() if self.last_loop_tick else None,
        }
