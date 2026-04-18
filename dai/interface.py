"""DAI entrypoint that drives the AutoLink subsystem.

DAI (Director AI) is the executive intelligence that lives inside AutoLink.
External callers should invoke `run_intelligence_task` (generic) or
`make_something` (maker loop) rather than reaching into AutoLink directly.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from auto.autolink import AutoLIP
from auto.models import AutoTask

# Singleton AutoLIP — DAI owns one routing substrate per process.
_AUTOLIP = AutoLIP()

# Maker modes — kept loose so new modes can be added without a migration.
MAKER_MODES = ("idea", "plan", "spec", "code_stub")


def run_intelligence_task(
    intent: str,
    payload: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    *,
    sensitivity: str = "normal",
    complexity: str = "normal",
    latency_budget_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """Run an intelligence task through AutoLink and return the result."""
    task = AutoTask(
        task_id=str(uuid.uuid4()),
        intent=intent,
        payload=dict(payload or {}),
        user_id=user_id,
        session_id=session_id,
        sensitivity=sensitivity,
        complexity=complexity,
        latency_budget_ms=latency_budget_ms,
    )
    return _AUTOLIP.run_task(task)


def make_something(request: Dict[str, Any]) -> Dict[str, Any]:
    """High-level 'maker' entrypoint.

    request shape:
        {
          "goal": str,
          "mode": "idea" | "plan" | "spec" | "code_stub" | None,
          "user_id": str,
          "session_id": str | None,
          "metadata": dict | None,
        }

    The call is routed through AutoLink via `run_intelligence_task` with
    intent="make" and a maker flag in metadata. A dedicated DAI planner is
    not required; if one is added later this function should defer to it.
    """
    goal = (request.get("goal") or "").strip()
    if not goal:
        raise ValueError("make_something: 'goal' is required")

    mode = request.get("mode") or "idea"
    user_id = request.get("user_id")
    session_id = request.get("session_id")
    metadata = dict(request.get("metadata") or {})
    metadata.setdefault("maker", True)
    metadata.setdefault("mode", mode)

    # Maker work benefits from higher-quality reasoning by default; callers
    # can override via metadata.
    complexity = metadata.get("complexity", "high")
    sensitivity = metadata.get("sensitivity", "normal")
    latency_budget_ms = metadata.get("latency_budget_ms")

    # TODO: when dai.planner lands, delegate here instead of calling
    # run_intelligence_task directly.
    result = run_intelligence_task(
        intent="make",
        payload={"goal": goal, "mode": mode, "metadata": metadata},
        user_id=user_id,
        session_id=session_id,
        sensitivity=sensitivity,
        complexity=complexity,
        latency_budget_ms=latency_budget_ms,
    )

    result["maker"] = {"goal": goal, "mode": mode}
    return result
