"""DAI.SubsystemArchitect — designs subsystems as DesignSpecs."""
from __future__ import annotations

from typing import Any

from dai.core import Agent, DesignSpec


class SubsystemArchitect(Agent):
    name = "DAI.SubsystemArchitect"

    def design(self, target: str, **ctx: Any) -> DesignSpec: ...
    def decompose(self, target: str) -> list[str]: ...
