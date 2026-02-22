"""Unified workspace runtime orchestrator.

WorkspaceRuntime is the central backend engine that wires everything together:
- mode selection (ModeManager)
- capability registration + dispatch (CapabilityRegistry)
- mode-aware routing (ContextualResolver -> ModeAwareRouter)
- task execution (TaskRunner)
- session state updates (SessionState)
- transcript writes (SessionTranscript)
- event emission (EventBus)
- runtime health tracking (RuntimeHealth)

All logic is placeholder-focused: it provides structure, debug hooks, and
extensibility, without implementing real OS automation or log parsing.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from core.capability_registry import CapabilityRegistry, DEFAULT_CAPABILITY_REGISTRY
from core.command_interpreter import Command
from core.debug_log import debug_log
from core.event_bus import EventBus, DEFAULT_EVENT_BUS
from core.mode_aware_router import ModeAwareRouter
from core.mode_manager import DEFAULT_MODE_MANAGER, Mode, ModeManager
from core.runtime_health import RuntimeHealth
from core.session_state import DEFAULT_SESSION_STATE, SessionState
from core.session_transcript import DEFAULT_SESSION_TRANSCRIPT, SessionTranscript
from core.task_runner import DEFAULT_TASK_RUNNER, TaskRunner
from core.contextual_resolver import DEFAULT_CONTEXTUAL_RESOLVER
from tools.automation_engine import DEFAULT_AUTOMATION_ENGINE, AutomationEngine, WorkflowSpec
from tools.insight_engine import DEFAULT_INSIGHT_ENGINE, InsightEngine
from tools.process_monitor import DEFAULT_PROCESS_MONITOR, ProcessMonitor, ProcessSpec


class WorkspaceRuntime:
    """Central orchestrator for the four-mode backend runtime."""

    def __init__(
        self,
        *,
        event_bus: EventBus = DEFAULT_EVENT_BUS,
        capabilities: CapabilityRegistry = DEFAULT_CAPABILITY_REGISTRY,
        mode_manager: ModeManager = DEFAULT_MODE_MANAGER,
        session_state: SessionState = DEFAULT_SESSION_STATE,
        transcript: SessionTranscript = DEFAULT_SESSION_TRANSCRIPT,
        task_runner: TaskRunner = DEFAULT_TASK_RUNNER,
        process_monitor: ProcessMonitor = DEFAULT_PROCESS_MONITOR,
        automation_engine: AutomationEngine = DEFAULT_AUTOMATION_ENGINE,
        insight_engine: InsightEngine = DEFAULT_INSIGHT_ENGINE,
    ) -> None:
        self.bus = event_bus
        self.capabilities = capabilities
        self.modes = mode_manager
        self.state = session_state
        self.transcript = transcript
        self.tasks = task_runner
        self.process_monitor = process_monitor
        self.automation_engine = automation_engine
        self.insight_engine = insight_engine

        self.health = RuntimeHealth(bus=self.bus, transcript=self.transcript)
        self.router = ModeAwareRouter(
            capabilities=self.capabilities,
            event_bus=self.bus,
            mode_manager=self.modes,
            resolver=DEFAULT_CONTEXTUAL_RESOLVER,
        )

        self._register_builtin_tasks()
        self._register_builtin_capabilities()
        self._install_health_listeners()

        debug_log("WorkspaceRuntime initialized", component="workspace_runtime")

    def _register_builtin_tasks(self) -> None:
        """Register a minimal set of built-in tasks."""

        self.tasks.register_task("monitor_process", self._task_monitor_process)
        self.tasks.register_task("run_workflow", self._task_run_workflow)
        self.tasks.register_task("debug_last_error", self._task_debug_last_error)
        self.tasks.register_task("insight_analyze", self._task_insight_analyze)

    def _register_builtin_capabilities(self) -> None:
        """Register core capabilities backed by tasks/engines."""

        def cap_mode_set(*, payload: dict[str, Any], agent: Any = None, command: Optional[Command] = None) -> dict[str, Any]:
            target = None
            if command and command.mode is not None:
                target = command.mode.value
            if not target:
                target = payload.get("mode")
            if not target:
                return {"status": "error", "error": "Missing target mode"}

            m = Mode(str(target))
            self.modes.set_mode(m, reason="capability: mode.set")
            self.state.set_mode(self.modes.get_mode())
            return {"status": "ok", "mode": m.value}

        def cap_process_monitor(*, payload: dict[str, Any], agent: Any = None, command: Optional[Command] = None) -> dict[str, Any]:
            spec = ProcessSpec(name=str(payload.get("name") or "placeholder"), argv=list(payload.get("argv") or []))
            task_id = self.tasks.run_task("monitor_process", spec=spec)
            self.state.set_active_task(task_id, {"name": "monitor_process"})
            self.transcript.append("task", "Started monitor_process", {"task_id": task_id, "name": spec.name})
            return {"status": "ok", "task_id": task_id, "task": "monitor_process"}

        def cap_debug_last_error(*, payload: dict[str, Any], agent: Any = None, command: Optional[Command] = None) -> dict[str, Any]:
            task_id = self.tasks.run_task("debug_last_error", agent=agent)
            self.state.set_active_task(task_id, {"name": "debug_last_error"})
            self.transcript.append("task", "Started debug_last_error", {"task_id": task_id})
            return {"status": "ok", "task_id": task_id, "task": "debug_last_error"}

        def cap_automation_run_workflow(*, payload: dict[str, Any], agent: Any = None, command: Optional[Command] = None) -> dict[str, Any]:
            wf = payload.get("workflow")
            if isinstance(wf, WorkflowSpec):
                workflow = wf
            elif isinstance(wf, dict):
                workflow = WorkflowSpec(name=str(wf.get("name") or "placeholder"), tasks=list(wf.get("tasks") or []))
            else:
                workflow = WorkflowSpec(name="placeholder", tasks=[])

            task_id = self.tasks.run_task("run_workflow", workflow=workflow, agent=agent)
            self.state.set_active_task(task_id, {"name": "run_workflow"})
            self.transcript.append("task", "Started run_workflow", {"task_id": task_id, "workflow": workflow.name})
            return {"status": "ok", "task_id": task_id, "task": "run_workflow"}

        def cap_insight_analyze(*, payload: dict[str, Any], agent: Any = None, command: Optional[Command] = None) -> dict[str, Any]:
            text = str(payload.get("text") or (command.raw if command else ""))
            task_id = self.tasks.run_task("insight_analyze", text=text)
            self.state.set_active_task(task_id, {"name": "insight_analyze"})
            self.transcript.append("task", "Started insight_analyze", {"task_id": task_id})
            return {"status": "ok", "task_id": task_id, "task": "insight_analyze"}

        self.capabilities.register_capability("mode.set", cap_mode_set, description="Switch active mode")
        self.capabilities.register_capability("process.monitor", cap_process_monitor, description="Monitor a process (placeholder)")
        self.capabilities.register_capability("debug.debug_last_error", cap_debug_last_error, description="Debug last error")
        self.capabilities.register_capability("automation.run_workflow", cap_automation_run_workflow, description="Run a workflow (placeholder)")
        self.capabilities.register_capability("insight.analyze", cap_insight_analyze, description="Analyze text/logs (placeholder)")

    def _install_health_listeners(self) -> None:
        """Subscribe to key events and update health metrics (placeholder)."""

        def on_task_error(event: Any) -> None:
            payload = getattr(event, "payload", {})
            self.health.record_task_failure(
                task_id=str(payload.get("task_id") or ""),
                name=str(payload.get("name") or ""),
                error=str(payload.get("error") or ""),
            )

        self.bus.subscribe("task.error", on_task_error)
        self.bus.subscribe("task.errored", on_task_error)

    def dispatch(self, command: Command, *, agent: Any = None, payload: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Dispatch a structured command through resolver -> router -> capability."""

        payload = dict(payload or {})
        self.health.tick_loop()

        debug_log(
            "Dispatching command",
            component="workspace_runtime",
            data={"kind": command.kind, "mode": command.mode.value if command.mode else None, "raw": command.raw},
        )
        self.bus.emit("command.dispatch", {"kind": command.kind, "raw": command.raw}, source="workspace_runtime")
        self.transcript.append("command", "Command dispatched", {"kind": command.kind, "raw": command.raw})

        # Keep session mode in sync.
        self.state.set_mode(self.modes.get_mode())

        if command.kind == "noop":
            return {"status": "noop"}

        if command.kind == "unknown":
            self.bus.emit("command.unknown", {"raw": command.raw}, source="workspace_runtime")
            self.transcript.append("error", "Unknown command", {"raw": command.raw})
            return {"status": "unknown", "raw": command.raw}

        try:
            result = self.router.route(command=command, payload=payload, session_state=self.state, agent=agent)
            self.transcript.append("result", "Capability result", {"status": result.get("status"), "keys": list(result.keys())})
            return result
        except Exception as exc:  # noqa: BLE001
            debug_log(
                "Capability dispatch raised",
                component="workspace_runtime",
                level="WARN",
                data={"error": str(exc)},
            )
            self.health.record_capability_error(capability="<unknown>", error=str(exc))
            self.state.set_last_error({"message": str(exc)})
            return {"status": "error", "error": str(exc)}

    # ---- Built-in task implementations ----

    def _task_monitor_process(self, *, spec: ProcessSpec) -> dict[str, Any]:
        debug_log("Task: monitor_process", component="workspace_runtime", data={"name": spec.name})
        handle = self.process_monitor.launch_process(spec)
        state = self.process_monitor.poll(handle)
        self.state.set_last_process_state(state)

        logs = self.process_monitor.collect_logs(handle)
        self.state.set_last_logs([{"ts": l.ts.isoformat(), "source": l.source, "message": l.message} for l in logs])

        # Placeholder: no crash simulation by default.
        error = self.process_monitor.detect_crash(handle)
        if error is not None:
            err_map = {
                "error_type": error.error_type,
                "exit_code": error.exit_code,
                "message": error.message,
                "detected_at": error.detected_at.isoformat(),
                "logs": [{"ts": l.ts.isoformat(), "source": l.source, "message": l.message} for l in error.logs],
            }
            self.state.set_last_error(err_map)
            self.bus.publish("process.crash", err_map, source="workspace_runtime")
            return {"status": "crashed", "error": err_map}

        self.bus.emit("process.state", state, source="workspace_runtime")
        return {"status": "ok", "process": {"pid": handle.pid, "name": handle.spec.name}, "state": state}

    def _task_run_workflow(self, *, workflow: WorkflowSpec, agent: Any = None) -> dict[str, Any]:
        debug_log("Task: run_workflow", component="workspace_runtime", data={"workflow": workflow.name})
        result = self.automation_engine.run_workflow(workflow, agent=agent)
        self.bus.emit("automation.result", {"status": result.status, "workflow": result.workflow}, source="workspace_runtime")
        return {
            "status": result.status,
            "workflow": result.workflow,
            "completed": list(result.completed_tasks),
            "failed_task": result.failed_task,
        }

    def _task_debug_last_error(self, *, agent: Any = None) -> dict[str, Any]:
        debug_log("Task: debug_last_error", component="workspace_runtime")
        if self.state.last_error is None:
            return {"status": "no_error"}

        debug_result: DebugResult = debug_error(
            self.state.last_error,
            agent=agent,
            context={"mode": self.state.current_mode.value},
        )
        mapped = {
            "status": debug_result.status,
            "summary": debug_result.summary,
            "suspected_root_causes": list(debug_result.suspected_root_causes),
            "next_steps": list(debug_result.next_steps),
            "used_agent": bool(debug_result.used_agent),
        }
        if debug_result.agent_output:
            mapped["agent_output"] = debug_result.agent_output

        self.state.append_debugging_result(mapped)
        self.bus.emit("debug.result", mapped, source="workspace_runtime")
        return mapped

    def _task_insight_analyze(self, *, text: str) -> dict[str, Any]:
        debug_log("Task: insight_analyze", component="workspace_runtime", data={"chars": len(text)})
        result = self.insight_engine.analyze(text=text)
        mapped = {
            "status": result.status,
            "summary": result.summary,
            "patterns": list(result.patterns),
            "highlights": list(result.highlights),
        }
        self.state.append_insight_result(mapped)
        self.bus.emit("insight.result", mapped, source="workspace_runtime")
        return mapped


DEFAULT_WORKSPACE_RUNTIME = WorkspaceRuntime()
