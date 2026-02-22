"""Process monitor placeholders.

This module intentionally does NOT perform real OS process orchestration yet.
Instead, it provides structured scaffolding for:
- Launching a "process" (simulated handle)
- Polling status and detecting crashes (placeholder)
- Collecting log lines (placeholder)
- Comparing timestamps (utility)

All functions emit `debug_log` entries to make behavior visible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from core.debug_log import debug_log
from core.event_bus import DEFAULT_EVENT_BUS, EventBus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class ProcessSpec:
    """Specification for a process that might be launched."""

    name: str
    argv: list[str] = field(default_factory=list)
    cwd: Optional[str] = None
    env: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProcessHandle:
    """Simulated handle representing a launched process."""

    pid: str
    spec: ProcessSpec
    started_at: datetime


@dataclass(frozen=True, slots=True)
class LogLine:
    """A single log line with timestamp and source."""

    ts: datetime
    source: str
    message: str


@dataclass(frozen=True, slots=True)
class ErrorData:
    """Structured crash/error representation returned by ProcessMonitor."""

    process: ProcessHandle
    detected_at: datetime
    error_type: str
    exit_code: Optional[int]
    message: str
    logs: list[LogLine] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ProcessMonitor:
    """Placeholder process monitor API."""

    def __init__(self, *, event_bus: EventBus = DEFAULT_EVENT_BUS) -> None:
        self._known: dict[str, ProcessHandle] = {}
        self._bus = event_bus
        debug_log("ProcessMonitor initialized", component="process_monitor")

    def launch_process(self, spec: ProcessSpec) -> ProcessHandle:
        """Simulate launching a process.

        This does not spawn a real OS process.
        """

        handle = ProcessHandle(pid=str(uuid4()), spec=spec, started_at=utc_now())
        self._known[handle.pid] = handle
        debug_log(
            "Process launch requested (placeholder)",
            component="process_monitor",
            data={"pid": handle.pid, "name": spec.name, "argv": spec.argv, "cwd": spec.cwd},
        )
        self._bus.emit(
            "process.launch_requested",
            {"pid": handle.pid, "name": spec.name, "argv": spec.argv, "cwd": spec.cwd},
            source="process_monitor",
        )
        return handle

    def poll(self, handle: ProcessHandle) -> dict[str, Any]:
        """Return placeholder status information for a process."""

        debug_log(
            "Polling process (placeholder)",
            component="process_monitor",
            data={"pid": handle.pid, "name": handle.spec.name},
        )
        state = {
            "pid": handle.pid,
            "running": True,
            "last_heartbeat": utc_now().isoformat(),
        }
        self._bus.emit("process.polled", state, source="process_monitor")
        return state

    def detect_crash(self, handle: ProcessHandle, *, simulate: bool = False) -> Optional[ErrorData]:
        """Placeholder crash detection.

        Returns None by default. Future implementations will inspect exit codes,
        stderr, health checks, and signal/exception metadata.
        """

        debug_log(
            "Crash detection check (placeholder)",
            component="process_monitor",
            data={"pid": handle.pid, "name": handle.spec.name, "simulate": simulate},
        )

        self._bus.emit(
            "process.crash_check",
            {"pid": handle.pid, "name": handle.spec.name, "simulate": simulate},
            source="process_monitor",
        )

        if not simulate:
            return None

        logs = [
            LogLine(ts=utc_now(), source="stdout", message=f"{handle.spec.name}: starting"),
            LogLine(ts=utc_now(), source="stderr", message=f"{handle.spec.name}: simulated crash"),
        ]
        error = ErrorData(
            process=handle,
            detected_at=utc_now(),
            error_type="SimulatedCrash",
            exit_code=1,
            message="Process crash simulated (placeholder).",
            logs=logs,
            metadata={"simulated": True},
        )
        debug_log(
            "Crash detected (simulated)",
            component="process_monitor",
            level="WARN",
            data={"pid": handle.pid, "name": handle.spec.name},
        )
        self._bus.emit(
            "process.crash_detected",
            {"pid": handle.pid, "name": handle.spec.name, "error_type": error.error_type, "exit_code": error.exit_code},
            source="process_monitor",
        )
        return error

    def collect_logs(self, handle: ProcessHandle, *, since: Optional[datetime] = None, limit: int = 200) -> list[LogLine]:
        """Placeholder log collection.

        This returns an empty list; future versions will tail files/streams.
        """

        debug_log(
            "Collecting logs (placeholder)",
            component="process_monitor",
            data={"pid": handle.pid, "since": since.isoformat() if since else None, "limit": limit},
        )
        self._bus.emit(
            "process.logs_collected",
            {"pid": handle.pid, "count": 0, "since": since.isoformat() if since else None, "limit": limit},
            source="process_monitor",
        )
        return []

    @staticmethod
    def compare_timestamps(a: datetime, b: datetime) -> dict[str, Any]:
        """Compare two timestamps and return structured delta info."""

        delta = (a - b).total_seconds()
        result = {
            "a": a.isoformat(),
            "b": b.isoformat(),
            "delta_seconds": delta,
            "a_after_b": delta > 0,
        }
        debug_log("Compared timestamps", component="process_monitor", data=result)
        return result


DEFAULT_PROCESS_MONITOR = ProcessMonitor()
