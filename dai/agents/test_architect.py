"""DAI.TestArchitect — designs test plans and validation harnesses."""
from __future__ import annotations

from typing import Any

from dai.core import Agent, DesignSpec


class TestArchitect(Agent):
    name = "DAI.TestArchitect"

    def design(self, target: str, **ctx: Any) -> DesignSpec: ...
    def plan_for(self, spec: DesignSpec) -> list[str]: ...
