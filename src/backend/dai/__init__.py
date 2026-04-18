"""DAI (Director AI) backend package."""

from .system_prompt import DAI_SYSTEM_PROMPT
from .mode_prompts import (
    ARCHITECT_PROMPT,
    DEBUGGER_PROMPT,
    ANALYST_PROMPT,
    BUILDER_PROMPT,
)
from .tone_registry import ToneDefinition, ToneRegistry, NewTone, register_tone
from .projection import Goal, Subtask, TimelineEvent, ChipRef, HealthStatus, DAIProjection
from .al_protocol import (
    RequestType,
    DAIRequest,
    ResponseChip,
    ALError,
    ResponseStatus,
    ALResponse,
)

__all__ = [
    # system prompt
    "DAI_SYSTEM_PROMPT",
    # mode prompts
    "ARCHITECT_PROMPT",
    "DEBUGGER_PROMPT",
    "ANALYST_PROMPT",
    "BUILDER_PROMPT",
    # tone registry
    "ToneDefinition",
    "ToneRegistry",
    "NewTone",
    "register_tone",
    # state projection
    "Goal",
    "Subtask",
    "TimelineEvent",
    "ChipRef",
    "HealthStatus",
    "DAIProjection",
    # AL protocol
    "RequestType",
    "DAIRequest",
    "ResponseChip",
    "ALError",
    "ResponseStatus",
    "ALResponse",
]
