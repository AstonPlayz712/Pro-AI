"""Global four-mode manager for the AI system.

Modes:
- Smart: default interaction and assistance.
- Debug: diagnosing failures and investigating process/tool issues.
- Automation: running workflows and task execution.
- Insight: analysis, summaries, and pattern discovery.

This module is intentionally lightweight and stateful. It can later be extended to
support per-workspace sessions, persistence, and UI sync.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from core.debug_log import debug_log
from core.event_bus import DEFAULT_EVENT_BUS, EventBus
from core.session_transcript import DEFAULT_SESSION_TRANSCRIPT, SessionTranscript


class Mode(str, Enum):
    """Supported operating modes for the system."""

    SMART = "smart"
    DEBUG = "debug"
    AUTOMATION = "automation"
    INSIGHT = "insight"


@dataclass(frozen=True, slots=True)
class ModeFlags:
    """Behavior flags that influence engine behavior by mode."""

    allow_agent_escalation: bool
    enable_process_monitor: bool
    enable_debugging: bool
    enable_automation: bool
    enable_insight: bool
    verbose_debug: bool


_DEFAULT_FLAGS: dict[Mode, ModeFlags] = {
    Mode.SMART: ModeFlags(
        allow_agent_escalation=False,
        enable_process_monitor=True,
        enable_debugging=False,
        enable_automation=False,
        enable_insight=False,
        verbose_debug=False,
    ),
    Mode.DEBUG: ModeFlags(
        allow_agent_escalation=True,
        enable_process_monitor=True,
        enable_debugging=True,
        enable_automation=False,
        enable_insight=False,
        verbose_debug=True,
    ),
    Mode.AUTOMATION: ModeFlags(
        allow_agent_escalation=True,
        enable_process_monitor=True,
        enable_debugging=True,
        enable_automation=True,
        enable_insight=False,
        verbose_debug=True,
    ),
    Mode.INSIGHT: ModeFlags(
        allow_agent_escalation=False,
        enable_process_monitor=False,
        enable_debugging=False,
        enable_automation=False,
        enable_insight=True,
        verbose_debug=False,
    ),
}


class ModeManager:
    """Manage global mode selection and mode-specific flags."""

    def __init__(
        self,
        initial_mode: Mode = Mode.SMART,
        *,
        event_bus: EventBus = DEFAULT_EVENT_BUS,
        transcript: SessionTranscript = DEFAULT_SESSION_TRANSCRIPT,
    ) -> None:
        self._mode: Mode = initial_mode
        self._flags_override: dict[Mode, ModeFlags] = {}
        self._bus = event_bus
        self._transcript = transcript

        debug_log(
            "Mode manager initialized",
            component="mode_manager",
            data={"mode": self._mode.value},
        )

    def set_mode(self, mode: Mode | str, *, reason: Optional[str] = None) -> Mode:
        """Set the active mode.

        Args:
            mode: Mode enum or mode string.
            reason: Optional reason for audit/debug logs.

        Returns:
            The active mode after the update.
        """

        next_mode = Mode(mode) if not isinstance(mode, Mode) else mode
        if next_mode == self._mode:
            debug_log(
                "Mode set requested but already active",
                component="mode_manager",
                data={"mode": self._mode.value, "reason": reason or ""},
            )
            return self._mode

        prev = self._mode
        self._mode = next_mode
        debug_log(
            "Mode changed",
            component="mode_manager",
            data={"from": prev.value, "to": next_mode.value, "reason": reason or ""},
        )

        self._bus.emit(
            "mode.changed",
            {"from": prev.value, "to": next_mode.value, "reason": reason or ""},
            source="mode_manager",
        )
        self._transcript.append(
            "mode",
            f"Mode changed: {prev.value} -> {next_mode.value}",
            {"from": prev.value, "to": next_mode.value, "reason": reason or ""},
        )
        return self._mode

    def get_mode(self) -> Mode:
        """Return the current active mode."""

        return self._mode

    def is_mode(self, mode: Mode | str) -> bool:
        """Check if the current mode matches the provided mode."""

        return self._mode == (Mode(mode) if not isinstance(mode, Mode) else mode)

    def get_flags(self, mode: Optional[Mode | str] = None) -> ModeFlags:
        """Return mode-specific behavior flags."""

        m = self._mode if mode is None else (Mode(mode) if not isinstance(mode, Mode) else mode)
        return self._flags_override.get(m) or _DEFAULT_FLAGS[m]

    def override_flags(self, mode: Mode | str, flags: ModeFlags) -> None:
        """Override flags for a mode (useful for tests/prototypes)."""

        m = Mode(mode) if not isinstance(mode, Mode) else mode
        self._flags_override[m] = flags
        debug_log(
            "Mode flags overridden",
            component="mode_manager",
            data={"mode": m.value, "flags": flags},
        )

    def clear_overrides(self) -> None:
        """Remove all flags overrides."""

        self._flags_override.clear()
        debug_log("Mode flags overrides cleared", component="mode_manager")


DEFAULT_MODE_MANAGER = ModeManager()


def set_mode(mode: Mode | str, *, reason: Optional[str] = None) -> Mode:
    """Convenience wrapper around the default mode manager."""

    return DEFAULT_MODE_MANAGER.set_mode(mode, reason=reason)


def get_mode() -> Mode:
    """Convenience wrapper around the default mode manager."""

    return DEFAULT_MODE_MANAGER.get_mode()


def is_mode(mode: Mode | str) -> bool:
    """Convenience wrapper around the default mode manager."""

    return DEFAULT_MODE_MANAGER.is_mode(mode)
