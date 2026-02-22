"""Debugging engine placeholder.

This engine accepts structured `error_data` (from process_monitor) and produces a
structured debugging result.

Behavior:
- If an AI agent is available, it escalates using agent_prompt_builder.
- Otherwise, it runs lightweight self-diagnosis heuristics.

No real code execution, log parsing, or external API calls are performed here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Protocol

from core.agent_prompt_builder import AgentPrompt, build_debug_prompt
from core.debug_log import debug_log
from core.event_bus import DEFAULT_EVENT_BUS, EventBus


class Agent(Protocol):
    """Minimal agent interface expected by the debugging engine."""

    def generate(self, prompt: AgentPrompt) -> str:  # pragma: no cover
        ...


@dataclass(frozen=True, slots=True)
class DebugResult:
    """Structured debugging outcome."""

    status: str
    summary: str
    suspected_root_causes: list[str]
    next_steps: list[str]
    used_agent: bool
    agent_output: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


def _fallback_heuristics(error_data: Mapping[str, Any]) -> DebugResult:
    message = str(error_data.get("message") or "")
    error_type = str(error_data.get("error_type") or "UnknownError")
    suspected: list[str] = []

    lowered = message.lower()
    if "out of memory" in lowered or ("cuda" in lowered and "memory" in lowered):
        suspected.append("Out-of-memory condition")
    if "permission" in lowered or "access denied" in lowered:
        suspected.append("Permissions or access control issue")
    if "timeout" in lowered or "timed out" in lowered:
        suspected.append("Timeout / hung process")
    if "not found" in lowered or "no such file" in lowered:
        suspected.append("Missing file or incorrect path")

    if not suspected:
        suspected.append(f"Generic failure: {error_type}")

    result = DebugResult(
        status="heuristic",
        summary=f"Fallback diagnosis for {error_type}",
        suspected_root_causes=suspected,
        next_steps=[
            "Capture recent logs around the failure timestamp",
            "Record environment details (OS, versions, configs)",
            "Reproduce with minimal inputs",
        ],
        used_agent=False,
        agent_output=None,
        metadata={"error_type": error_type},
    )

    debug_log(
        "Fallback heuristics produced result",
        component="debugging_engine",
        data={"suspected": suspected},
    )
    return result


def debug_error(
    error_data: Mapping[str, Any],
    *,
    agent: Optional[Agent | Callable[[AgentPrompt], str]] = None,
    context: Optional[Mapping[str, Any]] = None,
) -> DebugResult:
    """Diagnose an error event.

    Args:
        error_data: Structured error event (dict-like).
        agent: Optional AI agent or callable for escalation.
        context: Optional context to include in prompts.

    Returns:
        DebugResult describing the diagnosis.
    """

    debug_log(
        "Debugging engine invoked",
        component="debugging_engine",
        data={"has_agent": agent is not None, "context_keys": list((context or {}).keys())},
    )
    DEFAULT_EVENT_BUS.emit(
        "debug.invoked",
        {"has_agent": agent is not None, "context_keys": list((context or {}).keys())},
        source="debugging_engine",
    )

    if agent is None:
        DEFAULT_EVENT_BUS.emit("debug.fallback", {"reason": "no_agent"}, source="debugging_engine")
        return _fallback_heuristics(error_data)

    prompt = build_debug_prompt(error_data=error_data, context=context)
    debug_log("Escalating to agent", component="debugging_engine")
    DEFAULT_EVENT_BUS.emit("debug.escalating", {"prompt_keys": list(prompt.metadata.keys())}, source="debugging_engine")

    try:
        if callable(agent) and not hasattr(agent, "generate"):
            agent_text = agent(prompt)
        else:
            agent_text = agent.generate(prompt)  # type: ignore[union-attr]

        result = DebugResult(
            status="agent",
            summary="Agent-assisted diagnosis (placeholder)",
            suspected_root_causes=["Agent output attached"],
            next_steps=["Review agent suggestions", "Apply smallest safe change", "Re-run with monitoring"],
            used_agent=True,
            agent_output=str(agent_text),
            metadata={"prompt_metadata": prompt.metadata},
        )

        debug_log(
            "Agent returned debug output",
            component="debugging_engine",
            data={"chars": len(result.agent_output or "")},
        )
        DEFAULT_EVENT_BUS.emit(
            "debug.agent_result",
            {"chars": len(result.agent_output or "")},
            source="debugging_engine",
        )
        return result

    except Exception as exc:  # noqa: BLE001
        debug_log(
            "Agent escalation failed; falling back",
            component="debugging_engine",
            level="WARN",
            data={"error": str(exc)},
        )
        DEFAULT_EVENT_BUS.emit(
            "debug.agent_failed",
            {"error": str(exc)},
            source="debugging_engine",
        )
        return _fallback_heuristics(error_data)
