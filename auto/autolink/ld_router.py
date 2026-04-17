"""AutoLD — routing logic for AutoLink.

Decides whether a task should run on the on-device executor (AutoOD) or the
cloud executor (AutoClink), based on sensitivity, complexity, and latency
budget hints carried on the AutoTask.
"""
from __future__ import annotations

from ..models import AutoTask, ContextBundle, RouteDecision


class AutoLD:
    """Route AutoTasks to AutoOD or AutoClink."""

    # Latency below this threshold prefers on-device execution.
    _ON_DEVICE_LATENCY_THRESHOLD_MS = 250

    def route(self, task: AutoTask, context: ContextBundle) -> RouteDecision:
        # High-sensitivity work stays on device.
        if task.sensitivity == "high":
            return RouteDecision(
                target="AutoOD",
                reason="sensitivity=high → keep on device",
            )

        # Tight latency budgets prefer on device.
        if (
            task.latency_budget_ms is not None
            and task.latency_budget_ms <= self._ON_DEVICE_LATENCY_THRESHOLD_MS
        ):
            return RouteDecision(
                target="AutoOD",
                reason=f"latency_budget_ms={task.latency_budget_ms} → on device",
            )

        # High complexity goes to the cloud.
        if task.complexity == "high":
            return RouteDecision(
                target="AutoClink",
                reason="complexity=high → cloud execution",
            )

        # Default: on-device for lighter work.
        return RouteDecision(
            target="AutoOD",
            reason="default policy → on device",
        )
