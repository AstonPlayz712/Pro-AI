"""AutoLCE — context engine for AutoLink.

Assembles a ContextBundle from AutoLM memory plus a stub system_state. The
system_state hook is where future signals (device, network, sensors, active
PA mode, etc.) will be injected.
"""
from __future__ import annotations

from typing import Any, Dict

from ..models import AutoTask, ContextBundle
from .lm_memory import AutoLM


class AutoLCE:
    """Builds ContextBundles for tasks."""

    def __init__(self, memory: AutoLM) -> None:
        self._memory = memory

    def build_context(self, task: AutoTask) -> ContextBundle:
        memory = self._memory.load_memory(task.user_id)
        return ContextBundle(
            task_id=task.task_id,
            memory=memory,
            system_state=self._system_state(task),
            notes=[f"context built for intent={task.intent!r}"],
        )

    def _system_state(self, task: AutoTask) -> Dict[str, Any]:
        """Minimal system_state stub.

        TODO: enrich with device profile, network class, battery, active PA
        mode, sensor snapshot, etc.
        """
        return {
            "session_id": task.session_id,
            "user_id": task.user_id,
            "online": True,
        }
