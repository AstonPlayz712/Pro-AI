"""Capability taxonomy.

Defines a hierarchical classification for capabilities.

This is used by contextual_resolver and health reporting to group capabilities
under high-level domains (core, debug, automation, insight).

The taxonomy is intentionally simple: capabilities are classified by prefix.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CapabilityCategory:
    """Represents a taxonomy node."""

    key: str
    label: str


CORE = CapabilityCategory("core", "Core")
DEBUG = CapabilityCategory("debug", "Debug")
AUTOMATION = CapabilityCategory("automation", "Automation")
INSIGHT = CapabilityCategory("insight", "Insight")
PROCESS = CapabilityCategory("process", "Process")


def classify(capability_name: str) -> CapabilityCategory:
    """Classify a capability name into a top-level category."""

    name = capability_name.strip().lower()
    if name.startswith("debug."):
        return DEBUG
    if name.startswith("automation."):
        return AUTOMATION
    if name.startswith("insight."):
        return INSIGHT
    if name.startswith("process."):
        return PROCESS
    if name.startswith("mode.") or name.startswith("task.") or name.startswith("event."):
        return CORE
    return CORE


def list_categories() -> list[CapabilityCategory]:
    return [CORE, PROCESS, DEBUG, AUTOMATION, INSIGHT]
