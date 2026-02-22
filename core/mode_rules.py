"""Mode rules and behavior flags.

This module defines policy-style helpers that translate a mode into runtime
behavior decisions.

It complements `core.mode_manager` by providing higher-level predicates like:
- should_monitor_process()
- should_generate_agent_prompt()
- should_run_fallback_diagnostics()

Rules are intentionally simple and can be refined over time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.mode_manager import Mode, ModeFlags


@dataclass(frozen=True, slots=True)
class ModeBehavior:
    """Derived behavior decisions for a given mode."""

    flags: ModeFlags

    def should_monitor_process(self) -> bool:
        return self.flags.enable_process_monitor

    def should_enable_debugging(self) -> bool:
        return self.flags.enable_debugging

    def should_enable_automation(self) -> bool:
        return self.flags.enable_automation

    def should_enable_insight(self) -> bool:
        return self.flags.enable_insight

    def should_generate_agent_prompt(self, *, agent_available: bool) -> bool:
        return bool(agent_available and self.flags.allow_agent_escalation and self.flags.enable_debugging)

    def should_run_fallback_diagnostics(self, *, agent_available: bool) -> bool:
        return bool(self.flags.enable_debugging and (not agent_available or not self.flags.allow_agent_escalation))


def behavior_for(flags: ModeFlags) -> ModeBehavior:
    """Convert ModeFlags to derived behavior helpers."""

    return ModeBehavior(flags=flags)


def should_monitor_process(flags: ModeFlags) -> bool:
    return behavior_for(flags).should_monitor_process()


def should_generate_agent_prompt(flags: ModeFlags, *, agent_available: bool) -> bool:
    return behavior_for(flags).should_generate_agent_prompt(agent_available=agent_available)


def should_run_fallback_diagnostics(flags: ModeFlags, *, agent_available: bool) -> bool:
    return behavior_for(flags).should_run_fallback_diagnostics(agent_available=agent_available)
