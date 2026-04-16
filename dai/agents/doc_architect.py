"""DAI.DocArchitect — designs documentation structure and content."""
from __future__ import annotations

from typing import Any

from dai.core import Agent, DesignSpec


class DocArchitect(Agent):
    name = "DAI.DocArchitect"

    def design(self, target: str, **ctx: Any) -> DesignSpec: ...
    def design_readme(self, subsystem: str) -> DesignSpec: ...
    def design_guide(self, topic: str) -> DesignSpec: ...
