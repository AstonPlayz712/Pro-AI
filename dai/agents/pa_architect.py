"""DAI.PAArchitect — designs PA.MasterFlow Modes."""
from __future__ import annotations

from typing import Any

from dai.core import Agent, DesignSpec, PAModeSpec


class PAArchitect(Agent):
    name = "DAI.PAArchitect"

    def design(self, target: str, **ctx: Any) -> DesignSpec: ...

    # PA-specific API
    def design_mode(self, name: str, description: str, **ctx: Any) -> PAModeSpec: ...
    def build_routing_entry(self, mode_name: str) -> str: ...
    def build_validation(self, required_params: list[str]) -> str: ...
    def emit_branch_steps(self, name: str, ctx: dict[str, Any]) -> list[str]: ...
