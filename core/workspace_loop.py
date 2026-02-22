"""Workspace loop: central runtime loop (placeholder).

The loop:
- listens for commands (via an in-memory queue)
- applies mode rules
- routes to engines/tasks through capability_registry and task_runner
- updates session_state
- writes entries to session_transcript
- emits events via event_bus

No real IPC or UI integration is implemented yet.
"""

from __future__ import annotations

import queue
from dataclasses import asdict
from typing import Any, Mapping, Optional

from core.command_surface import CommandSurface, DEFAULT_COMMAND_SURFACE
from core.debug_log import debug_log
from core.event_bus import EventBus, DEFAULT_EVENT_BUS
from core.mode_manager import ModeManager, DEFAULT_MODE_MANAGER
from core.mode_rules import behavior_for
from core.session_state import SessionState, DEFAULT_SESSION_STATE
from core.session_transcript import SessionTranscript, DEFAULT_SESSION_TRANSCRIPT
from core.task_runner import TaskRunner, DEFAULT_TASK_RUNNER
from core.workspace_runtime import WorkspaceRuntime, DEFAULT_WORKSPACE_RUNTIME


class WorkspaceLoop:
    """Central runtime loop for processing commands."""

    def __init__(
        self,
        *,
        event_bus: EventBus = DEFAULT_EVENT_BUS,
        command_surface: CommandSurface = DEFAULT_COMMAND_SURFACE,
        mode_manager: ModeManager = DEFAULT_MODE_MANAGER,
        session_state: SessionState = DEFAULT_SESSION_STATE,
        transcript: SessionTranscript = DEFAULT_SESSION_TRANSCRIPT,
        task_runner: TaskRunner = DEFAULT_TASK_RUNNER,
        runtime: WorkspaceRuntime = DEFAULT_WORKSPACE_RUNTIME,
    ) -> None:
        self.bus = event_bus
        self.surface = command_surface
        self.modes = mode_manager
        self.state = session_state
        self.transcript = transcript
        self.tasks = task_runner
        self.runtime = runtime

        self._inbox: queue.Queue[tuple[Any, dict[str, Any]]] = queue.Queue()
        self._running = False

        debug_log("WorkspaceLoop initialized", component="workspace_loop")

    def enqueue_command(self, command: Any, *, payload: Optional[Mapping[str, Any]] = None) -> None:
        """Enqueue a command for processing."""

        self._inbox.put((command, dict(payload or {})))
        debug_log(
            "Command enqueued",
            component="workspace_loop",
            data={"type": type(command).__name__},
        )
        self.bus.emit("loop.enqueued", {"type": type(command).__name__}, source="workspace_loop")

    def submit_command(self, command: Any, *, payload: Optional[Mapping[str, Any]] = None) -> None:
        """Backward-compatible alias for enqueue_command()."""

        self.enqueue_command(command, payload=payload)

    def process_next(self, *, agent: Any = None, timeout: float = 0.0) -> Optional[dict[str, Any]]:
        """Process a single queued command if available."""

        try:
            command, payload = self._inbox.get(timeout=timeout)
        except queue.Empty:
            return None

        self.runtime.health.tick_loop()
        self.bus.emit("loop.dequeued", {"type": type(command).__name__}, source="workspace_loop")
        self.transcript.append("command", "Command dequeued", {"type": type(command).__name__})

        # Apply mode rules (placeholder: currently uses ModeManager flags only).
        flags = self.modes.get_flags(self.modes.get_mode())
        behavior = behavior_for(flags)
        self.transcript.append("mode", "Mode behavior evaluated", {"mode": self.modes.get_mode().value, "flags": asdict(flags)})

        result = self.surface.submit(command, payload=payload, agent=agent)

        # Update session state with notable outcomes.
        if result.get("status") == "error":
            self.state.set_last_error({"message": result.get("error", "unknown")})
            self.transcript.append("error", "Command error", {"error": result.get("error")})
        else:
            self.transcript.append("result", "Command result", {"status": result.get("status"), "keys": list(result.keys())})

        self.bus.emit("loop.processed", {"status": result.get("status")}, source="workspace_loop")
        return result

    def run_once(self, *, agent: Any = None, timeout: float = 0.0) -> Optional[dict[str, Any]]:
        """Backward-compatible alias for process_next()."""

        return self.process_next(agent=agent, timeout=timeout)

    def run_forever(self, *, agent: Any = None) -> None:
        """Run until stop() is called (blocking)."""

        self._running = True
        debug_log("Workspace loop started", component="workspace_loop")
        self.bus.emit("loop.started", {}, source="workspace_loop")
        while self._running:
            _ = self.process_next(agent=agent, timeout=0.1)

    def stop(self) -> None:
        self._running = False
        debug_log("Workspace loop stopped", component="workspace_loop")
        self.bus.emit("loop.stopped", {}, source="workspace_loop")
