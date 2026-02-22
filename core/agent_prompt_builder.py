"""Prompt builder for escalating debugging tasks to an AI agent.

When Debugging Mode encounters an error event, this module assembles a structured
prompt containing:
- Crash metadata (timestamps, exit codes, exception types)
- Log excerpts (tail/head samples)
- Contextual hints (mode, task/workflow names)

This is intentionally a scaffold: it formats content but does not contact any
model or external service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from core.debug_log import debug_log


@dataclass(frozen=True, slots=True)
class AgentPrompt:
    """Structured prompt ready to send to an AI agent."""

    system: str
    user: str
    metadata: dict[str, Any]


def build_debug_prompt(
    *,
    error_data: Mapping[str, Any],
    context: Optional[Mapping[str, Any]] = None,
    max_log_chars: int = 4000,
) -> AgentPrompt:
    """Build a structured debug prompt.

    Args:
        error_data: Structured error information.
        context: Optional extra context (e.g., current mode, workflow name).
        max_log_chars: Soft cap for included log excerpts.

    Returns:
        AgentPrompt containing system/user messages and metadata.
    """

    ctx = dict(context or {})
    logs = error_data.get("logs") or []
    log_text = "\n".join(str(line) for line in logs)
    if len(log_text) > max_log_chars:
        log_text = log_text[-max_log_chars:]

    system = (
        "You are a debugging assistant. "
        "You receive structured crash metadata and log excerpts. "
        "Provide a focused diagnosis, likely root causes, and a safe next step plan. "
        "If information is missing, ask for the minimal missing details."
    )

    user_parts: list[str] = [
        "Crash Metadata:",
        str({k: error_data.get(k) for k in sorted(error_data.keys()) if k != "logs"}),
        "",
        "Context:",
        str(ctx),
        "",
        "Log Excerpts:",
        log_text or "<no logs available>",
    ]
    user = "\n".join(user_parts)

    prompt = AgentPrompt(
        system=system,
        user=user,
        metadata={
            "context": ctx,
            "error_data": dict(error_data),
            "max_log_chars": max_log_chars,
        },
    )

    debug_log(
        "Built agent debug prompt",
        component="agent_prompt_builder",
        data={"has_logs": bool(log_text), "context_keys": list(ctx.keys())},
    )
    return prompt
