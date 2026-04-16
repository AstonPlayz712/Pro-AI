"""DAI.UXArchitect — designs UX flows, screens, and states."""
from __future__ import annotations

from typing import Any

from dai.core import Agent, DesignSpec


class UXArchitect(Agent):
    name = "DAI.UXArchitect"

    def design(self, target: str, **ctx: Any) -> DesignSpec: ...
    def design_screen(self, name: str, **ctx: Any) -> DesignSpec: ...
    def design_flow(self, name: str, **ctx: Any) -> DesignSpec: ...
