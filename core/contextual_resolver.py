"""Contextual capability resolver.

Given a parsed Command, current mode, and session state, choose the best matching
capability for execution.

This is intentionally heuristic and placeholder-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from core.capability_registry import CapabilityRegistry
from core.command_interpreter import Command
from core.mode_manager import Mode


@dataclass(frozen=True, slots=True)
class Resolution:
    """Resolver output."""

    capability: str
    confidence: float
    reason: str


class ContextualResolver:
    """Heuristic resolver for mapping commands to capabilities."""

    def resolve(
        self,
        *,
        command: Command,
        payload: Mapping[str, Any],
        mode: Mode,
        session_state: Any,
        capabilities: CapabilityRegistry,
    ) -> Optional[Resolution]:
        # Explicit override.
        if "capability" in payload:
            cap = str(payload["capability"])
            if capabilities.get_capability(cap):
                return Resolution(capability=cap, confidence=1.0, reason="explicit_payload")

        # Mode change.
        if command.kind == "set_mode" and command.mode is not None:
            return Resolution(capability="mode.set", confidence=1.0, reason="set_mode_command")

        text = (payload.get("text") or command.raw or "").lower()

        # Debug intent.
        if any(k in text for k in ["debug", "crash", "error", "stack", "trace", "exception"]):
            if capabilities.get_capability("debug.debug_last_error"):
                return Resolution("debug.debug_last_error", 0.75, "debug_keywords")

        # Automation intent.
        if any(k in text for k in ["automate", "automation", "workflow", "run task", "execute", "batch"]):
            if capabilities.get_capability("automation.run_workflow"):
                return Resolution("automation.run_workflow", 0.7, "automation_keywords")

        # Insight intent.
        if any(k in text for k in ["insight", "analyze", "analyse", "summarize", "summary", "pattern"]):
            if capabilities.get_capability("insight.analyze"):
                return Resolution("insight.analyze", 0.7, "insight_keywords")

        # Default routing by mode.
        if mode == Mode.INSIGHT and capabilities.get_capability("insight.analyze"):
            return Resolution("insight.analyze", 0.6, "mode_default")
        if mode == Mode.AUTOMATION and capabilities.get_capability("automation.run_workflow"):
            return Resolution("automation.run_workflow", 0.6, "mode_default")
        if mode == Mode.DEBUG and capabilities.get_capability("debug.debug_last_error"):
            return Resolution("debug.debug_last_error", 0.6, "mode_default")

        if capabilities.get_capability("process.monitor"):
            return Resolution("process.monitor", 0.55, "fallback_process_monitor")

        return None


DEFAULT_CONTEXTUAL_RESOLVER = ContextualResolver()
