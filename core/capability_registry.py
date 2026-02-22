"""Capability registry for the unified runtime.

Engines and subsystems register capabilities (name -> handler). The command surface
and workspace loop can then dispatch requests to these capabilities.

This is a lightweight in-process registry (no discovery, no permissions yet).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from core.debug_log import debug_log


CapabilityHandler = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class Capability:
    """Registered capability metadata."""

    name: str
    handler: CapabilityHandler
    description: str = ""


class CapabilityRegistry:
    """In-memory capability registry."""

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}
        debug_log("CapabilityRegistry initialized", component="capability_registry")

    def register_capability(self, name: str, handler: CapabilityHandler, *, description: str = "") -> None:
        """Register or replace a capability handler."""

        self._capabilities[name] = Capability(name=name, handler=handler, description=description)
        debug_log(
            "Capability registered",
            component="capability_registry",
            data={"name": name, "description": description},
        )

    def get_capability(self, name: str) -> Optional[Capability]:
        """Return a capability by name, or None if missing."""

        return self._capabilities.get(name)

    def list_capabilities(self) -> list[Capability]:
        """Return a list of all registered capabilities."""

        return [self._capabilities[name] for name in sorted(self._capabilities.keys())]


DEFAULT_CAPABILITY_REGISTRY = CapabilityRegistry()
