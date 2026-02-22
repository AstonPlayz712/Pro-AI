"""Mutable session state for the unified runtime.

SessionState is the single source of truth for:
- current mode
- active tasks
- last observed error/logs/process state
- debugging history
- insight results

This is intentionally in-memory only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from core.debug_log import debug_log
from core.mode_manager import Mode


@dataclass(slots=True)
class SessionState:
    """Holds runtime state with debug hooks."""

    current_mode: Mode = Mode.SMART
    active_tasks: dict[str, dict[str, Any]] = field(default_factory=dict)
    last_error: Optional[dict[str, Any]] = None
    last_logs: list[Any] = field(default_factory=list)
    last_process_state: Optional[dict[str, Any]] = None
    debugging_history: list[dict[str, Any]] = field(default_factory=list)
    insight_results: list[dict[str, Any]] = field(default_factory=list)

    def set_mode(self, mode: Mode) -> None:
        prev = self.current_mode
        self.current_mode = mode
        debug_log(
            "Session mode updated",
            component="session_state",
            data={"from": prev.value, "to": mode.value},
        )

    def get_mode(self) -> Mode:
        return self.current_mode

    def set_active_task(self, task_id: str, task_info: dict[str, Any]) -> None:
        self.active_tasks[task_id] = dict(task_info)
        debug_log(
            "Active task set",
            component="session_state",
            data={"task_id": task_id, "keys": list(task_info.keys())},
        )

    def clear_active_task(self, task_id: str) -> None:
        existed = task_id in self.active_tasks
        self.active_tasks.pop(task_id, None)
        debug_log(
            "Active task cleared",
            component="session_state",
            data={"task_id": task_id, "existed": existed},
        )

    def set_last_error(self, error: Optional[dict[str, Any]]) -> None:
        self.last_error = dict(error) if error is not None else None
        debug_log(
            "Last error updated",
            component="session_state",
            data={"has_error": self.last_error is not None},
        )

    def set_last_logs(self, logs: list[Any]) -> None:
        self.last_logs = list(logs)
        debug_log(
            "Last logs updated",
            component="session_state",
            data={"count": len(self.last_logs)},
        )

    def set_last_process_state(self, state: Optional[dict[str, Any]]) -> None:
        self.last_process_state = dict(state) if state is not None else None
        debug_log(
            "Last process state updated",
            component="session_state",
            data={"has_state": self.last_process_state is not None},
        )

    def append_debugging_result(self, result: dict[str, Any]) -> None:
        self.debugging_history.append(dict(result))
        debug_log(
            "Debugging history appended",
            component="session_state",
            data={"count": len(self.debugging_history)},
        )

    def append_insight_result(self, result: dict[str, Any]) -> None:
        self.insight_results.append(dict(result))
        debug_log(
            "Insight results appended",
            component="session_state",
            data={"count": len(self.insight_results)},
        )


DEFAULT_SESSION_STATE = SessionState()
