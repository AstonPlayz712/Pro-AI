"""Execution engines for AutoLink.

- AutoOD     — on-device executor stub
- AutoClink  — cloud executor stub

Both engines currently echo the payload back. TODO: wire to real on-device
inference and to the cloud model gateway respectively.
"""
from __future__ import annotations

from typing import Any, Dict

from ..models import AutoTask, ContextBundle


class AutoOD:
    """On-device executor (stub)."""

    name = "AutoOD"

    def execute(self, task: AutoTask, context: ContextBundle) -> Dict[str, Any]:
        # TODO: dispatch to local on-device model / tool runner.
        return {
            "engine": self.name,
            "task_id": task.task_id,
            "intent": task.intent,
            "payload": dict(task.payload),
            "context_notes": list(context.notes),
        }


class AutoClink:
    """Cloud executor (stub)."""

    name = "AutoClink"

    def execute(self, task: AutoTask, context: ContextBundle) -> Dict[str, Any]:
        # TODO: dispatch to cloud model gateway / remote tools.
        return {
            "engine": self.name,
            "task_id": task.task_id,
            "intent": task.intent,
            "payload": dict(task.payload),
            "context_notes": list(context.notes),
        }
