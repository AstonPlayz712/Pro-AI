"""Mode-aware command router.

Routes commands through:
- contextual_resolver -> capability name
- capability_registry -> handler

Applies mode rules to allow/deny certain capabilities.

This is placeholder logic meant to be extended with permissions, contexts, and
multi-step routing.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping, Optional

from core.capability_registry import CapabilityRegistry
from core.command_interpreter import Command
from core.contextual_resolver import ContextualResolver, Resolution, DEFAULT_CONTEXTUAL_RESOLVER
from core.debug_log import debug_log
from core.event_bus import EventBus
from core.mode_manager import Mode, ModeManager
from core.mode_rules import behavior_for


class ModeAwareRouter:
    """Dispatch commands to capabilities based on mode + resolver output."""

    def __init__(
        self,
        *,
        capabilities: CapabilityRegistry,
        event_bus: EventBus,
        mode_manager: ModeManager,
        resolver: ContextualResolver = DEFAULT_CONTEXTUAL_RESOLVER,
    ) -> None:
        self.capabilities = capabilities
        self.bus = event_bus
        self.modes = mode_manager
        self.resolver = resolver

    def route(
        self,
        *,
        command: Command,
        payload: Mapping[str, Any],
        session_state: Any,
        agent: Any = None,
    ) -> dict[str, Any]:
        mode = self.modes.get_mode()
        flags = self.modes.get_flags(mode)
        behavior = behavior_for(flags)

        resolution = self.resolver.resolve(
            command=command,
            payload=payload,
            mode=mode,
            session_state=session_state,
            capabilities=self.capabilities,
        )
        if resolution is None:
            self.bus.emit("router.unroutable", {"raw": command.raw, "kind": command.kind}, source="mode_aware_router")
            return {"status": "unroutable", "command": asdict(command)}

        # Mode gating (placeholder).
        cap = resolution.capability
        if cap.startswith("automation.") and not behavior.should_enable_automation():
            self.bus.emit("router.denied", {"capability": cap, "mode": mode.value}, source="mode_aware_router")
            return {"status": "denied", "reason": "automation_disabled", "capability": cap, "mode": mode.value}
        if cap.startswith("debug.") and not behavior.should_enable_debugging():
            self.bus.emit("router.denied", {"capability": cap, "mode": mode.value}, source="mode_aware_router")
            return {"status": "denied", "reason": "debugging_disabled", "capability": cap, "mode": mode.value}
        if cap.startswith("insight.") and not behavior.should_enable_insight():
            self.bus.emit("router.denied", {"capability": cap, "mode": mode.value}, source="mode_aware_router")
            return {"status": "denied", "reason": "insight_disabled", "capability": cap, "mode": mode.value}

        capability = self.capabilities.get_capability(cap)
        if capability is None:
            self.bus.emit("capability.missing", {"name": cap}, source="mode_aware_router")
            return {"status": "missing_capability", "capability": cap}

        debug_log(
            "Routing to capability",
            component="mode_aware_router",
            data={"capability": cap, "confidence": resolution.confidence, "reason": resolution.reason},
        )
        self.bus.emit(
            "capability.dispatch",
            {"name": cap, "confidence": resolution.confidence, "reason": resolution.reason},
            source="mode_aware_router",
        )

        out = capability.handler(payload=dict(payload), agent=agent, command=command)
        if isinstance(out, dict):
            return out
        return {"status": "ok", "capability": cap, "result": out}
