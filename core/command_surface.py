"""Command surface: single entry point for backend commands.

The command surface accepts either:
- natural language (str)
- structured command objects (core.command_interpreter.Command)
- structured dict payloads (e.g., {'capability': 'insight.analyze', ...})

It resolves input using:
- command_interpreter (for NL -> Command)
- capability_registry (for dispatch)

It emits events via event_bus and returns structured results.

This module is deliberately conservative (placeholder). The workspace loop is
responsible for continuous command processing and transcript writes.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping, Optional

from core.command_interpreter import Command, interpret
from core.debug_log import debug_log
from core.event_bus import EventBus, DEFAULT_EVENT_BUS
from core.mode_manager import Mode, ModeManager, DEFAULT_MODE_MANAGER
from core.workspace_runtime import WorkspaceRuntime, DEFAULT_WORKSPACE_RUNTIME


def _as_payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    return {"value": value}


class CommandSurface:
    """Single entry point for issuing commands into the backend runtime."""

    def __init__(
        self,
        *,
        event_bus: EventBus = DEFAULT_EVENT_BUS,
        mode_manager: ModeManager = DEFAULT_MODE_MANAGER,
        runtime: WorkspaceRuntime = DEFAULT_WORKSPACE_RUNTIME,
    ) -> None:
        self.bus = event_bus
        self.modes = mode_manager
        self.runtime = runtime
        debug_log("CommandSurface initialized", component="command_surface")

    def submit(
        self,
        command: str | Command | Mapping[str, Any],
        *,
        payload: Optional[Mapping[str, Any]] = None,
        agent: Any = None,
        apply_interpretation: bool = True,
    ) -> dict[str, Any]:
        """Submit a command to the backend.

        Args:
            command: Natural-language string, Command, or structured dict.
            payload: Optional payload dict.
            agent: Optional agent for debugging escalation.
            apply_interpretation: If True and command is str, allow interpret() to apply mode changes.

        Returns:
            Structured result.
        """

        base_payload = _as_payload(payload)
        self.bus.emit("command.received", {"type": type(command).__name__}, source="command_surface")

        try:
            if isinstance(command, str):
                # Do not mutate mode at interpretation time; mode changes are handled via capabilities.
                cmd = interpret(command, mode_manager=self.modes, apply=False)
                base_payload.setdefault("text", command)
            elif isinstance(command, Command):
                cmd = command
            else:
                # Structured dict: either direct capability call or a serialized Command.
                d = dict(command)
                if "capability" in d:
                    cap = str(d["capability"])
                    cap_payload = dict(d.get("payload") or {})
                    cap_payload.update(base_payload)
                    cmd = Command(
                        raw=f"capability:{cap}",
                        kind="capability",
                        mode=None,
                        confidence=1.0,
                        matched_phrase="",
                    )
                    return self.runtime.dispatch(cmd, agent=agent, payload={"capability": cap, **cap_payload})

                cmd = Command(
                    raw=str(d.get("raw") or ""),
                    kind=str(d.get("kind") or "unknown"),
                    mode=Mode(str(d["mode"])) if d.get("mode") else None,
                    confidence=float(d.get("confidence") or 0.0),
                    matched_phrase=str(d.get("matched_phrase") or ""),
                )

            result = self.runtime.dispatch(cmd, agent=agent, payload=base_payload)
            self.bus.emit("command.result", {"status": result.get("status")}, source="command_surface")
            return result

        except Exception as exc:  # noqa: BLE001
            debug_log(
                "CommandSurface error",
                component="command_surface",
                level="WARN",
                data={"error": str(exc)},
            )
            self.bus.emit("command.error", {"error": str(exc)}, source="command_surface")
            return {"status": "error", "error": str(exc)}



DEFAULT_COMMAND_SURFACE = CommandSurface()
