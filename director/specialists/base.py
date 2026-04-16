"""
base.py — BaseSpecialist: the contract all specialist agents must implement.

Each specialist:
  - receives a DAIRequest (possibly a subclass)
  - has access to shared vision and web tools injected by the DAI
  - returns a DAIResponse (possibly a subclass)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from director.core.schema import DAIRequest, DAIResponse

if TYPE_CHECKING:
    from director.tools.vision.interface import VisionInterface
    from director.tools.web.interface import WebInterface


class BaseSpecialist(ABC):
    """
    Abstract base class for all specialist agents.

    Attributes set by the Router before `run` is called
    ---------------------------------------------------
    matched_score : float   — routing confidence score (0–1)
    vision_tool   : VisionInterface
    web_tool      : WebInterface
    """

    matched_score: float = 0.0
    vision_tool:   "VisionInterface"
    web_tool:      "WebInterface"

    @abstractmethod
    def run(self, request: DAIRequest) -> DAIResponse:
        """
        Execute the specialist's diagnostic / resolution logic.

        Must always return a populated DAIResponse (or subclass).
        Must never raise — catch all exceptions internally and set
        DAIResponse.error instead.
        """
