"""DAI.CodeArchitect — designs multi-file code layouts."""
from __future__ import annotations

from typing import Any

from dai.core import Agent, DesignSpec


class CodeArchitect(Agent):
    name = "DAI.CodeArchitect"

    def design(self, target: str, **ctx: Any) -> DesignSpec: ...
    def plan_files(self, spec: DesignSpec) -> list[str]: ...
    def emit_stubs(self, spec: DesignSpec) -> dict[str, str]: ...
