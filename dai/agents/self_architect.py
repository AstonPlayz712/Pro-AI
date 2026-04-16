"""
DAI.SelfArchitect — designs new DAI modules and evolves system_map.yaml.

This is the only agent with `edit_system_map` privilege. All other agents
must route structural changes through here so the evolution log stays honest.
"""
from __future__ import annotations

from typing import Any

from dai.core import Agent, DesignSpec, Registry


class SelfArchitect(Agent):
    name = "DAI.SelfArchitect"

    def __init__(self, registry: Registry) -> None:
        self.registry = registry

    def design(self, target: str, **ctx: Any) -> DesignSpec: ...

    # Evolution API
    def propose_module(self, name: str, role: str, **ctx: Any) -> DesignSpec: ...
    def apply(self, proposal: DesignSpec) -> None: ...
    def migration_plan(self, proposal: DesignSpec) -> list[str]: ...
