"""AutoLIP — integration points for AutoLink.

AutoLIP is the single entrypoint into the AutoLink subsystem. It wires
together AutoLM (memory), AutoLCE (context), AutoLD (routing) and the
execution engines (AutoOD / AutoClink), and exposes hooks where security
layers (AutoTrust, AutoLS) will plug in later.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from ..models import AutoTask
from .engines import AutoClink, AutoOD
from .lce_context import AutoLCE
from .ld_router import AutoLD
from .lm_memory import AutoLM


class AutoLIP:
    """Main entrypoint into AutoLink."""

    def __init__(
        self,
        memory: Optional[AutoLM] = None,
        context: Optional[AutoLCE] = None,
        router: Optional[AutoLD] = None,
        on_device: Optional[AutoOD] = None,
        cloud: Optional[AutoClink] = None,
    ) -> None:
        self.memory = memory or AutoLM()
        self.context = context or AutoLCE(self.memory)
        self.router = router or AutoLD()
        self.on_device = on_device or AutoOD()
        self.cloud = cloud or AutoClink()

    def run_task(self, task: AutoTask) -> Dict[str, Any]:
        # TODO: AutoTrust/AutoLS security precheck hook.
        self._security_precheck(task)

        # 1. Load memory.
        memory_snapshot = self.memory.load_memory(task.user_id)

        # 2. Build context (LCE pulls fresh memory + system_state stub).
        # TODO: richer system_state (device, network, sensors, active PA mode).
        context = self.context.build_context(task)

        # 3. Compute routing.
        decision = self.router.route(task, context)

        # 4. Dispatch to the chosen executor.
        if decision.target == "AutoOD":
            engine_result = self.on_device.execute(task, context)
        elif decision.target == "AutoClink":
            engine_result = self.cloud.execute(task, context)
        else:
            raise ValueError(f"Unknown route target: {decision.target!r}")

        # 5. Persist a lightweight memory trace.
        # TODO: advanced memory (summaries, embeddings, eviction policy).
        self.memory.save_memory(
            task.user_id,
            {
                "task_id": task.task_id,
                "intent": task.intent,
                "route": decision.target,
            },
        )

        response = {
            "task_id": task.task_id,
            "intent": task.intent,
            "route": {
                "target": decision.target,
                "reason": decision.reason,
                "confidence": decision.confidence,
            },
            "context": {
                "memory_size": len(memory_snapshot),
                "system_state": dict(context.system_state),
                "notes": list(context.notes),
            },
            "result": engine_result,
        }

        # TODO: AutoTrust/AutoLS security postcheck hook.
        self._security_postcheck(task, response)

        return response

    # ------------------------------------------------------------------ #
    # Security hooks — intentionally no-ops until AutoTrust/AutoLS land. #
    # ------------------------------------------------------------------ #

    def _security_precheck(self, task: AutoTask) -> None:
        """TODO: AutoTrust/AutoLS will validate the task here."""
        return None

    def _security_postcheck(
        self, task: AutoTask, response: Dict[str, Any]
    ) -> None:
        """TODO: AutoTrust/AutoLS will sanitise the response here."""
        return None
