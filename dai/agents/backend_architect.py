"""DAI.BackendArchitect — designs backend endpoints and services."""
from __future__ import annotations

from typing import Any

from dai.core import Agent, DesignSpec


class BackendArchitect(Agent):
    name = "DAI.BackendArchitect"

    def design(self, target: str, **ctx: Any) -> DesignSpec: ...
    def design_endpoint(self, path: str, method: str, **ctx: Any) -> DesignSpec: ...
    def design_service(self, name: str, **ctx: Any) -> DesignSpec: ...
