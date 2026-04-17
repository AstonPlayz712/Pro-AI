"""DAI entrypoint that drives the AutoLink subsystem.

DAI (Director AI) is the executive intelligence that lives inside AutoLink.
External callers should invoke `run_intelligence_task` rather than reaching
into AutoLink components directly.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from auto.autolink import AutoLIP
from auto.models import AutoTask

# Singleton AutoLIP — DAI owns one routing substrate per process.
_AUTOLIP = AutoLIP()


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
