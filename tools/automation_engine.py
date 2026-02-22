"""Automation engine placeholders.

This engine represents the Automation Mode core runtime.

Important: This module does NOT implement real OS/UI automation.
It provides:
- Structured workflow/task definitions
- Placeholder execution loop
- Integration points with ProcessMonitor and DebuggingEngine

All actions are logged via debug_log.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from core.debug_log import debug_log
from core.event_bus import DEFAULT_EVENT_BUS, EventBus
from tools.process_monitor import DEFAULT_PROCESS_MONITOR, ErrorData, ProcessMonitor, ProcessSpec
from tools.debugging_engine import DebugResult, debug_error


@dataclass(frozen=True, slots=True)
class AutomationTask:
    """Single automation task (placeholder)."""

    name: str
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkflowSpec:
    """Workflow definition as a series of tasks."""

    name: str
    tasks: list[AutomationTask]


@dataclass(frozen=True, slots=True)
class AutomationResult:
    """Structured workflow execution result."""

    status: str
    workflow: str
    completed_tasks: list[str]
    failed_task: Optional[str]
    debug_result: Optional[DebugResult]
    metadata: dict[str, Any] = field(default_factory=dict)


class AutomationEngine:
    """Placeholder automation engine with monitoring and debugging integration."""

    def __init__(
        self,
        *,
        process_monitor: ProcessMonitor = DEFAULT_PROCESS_MONITOR,
        event_bus: EventBus = DEFAULT_EVENT_BUS,
    ) -> None:
        self.process_monitor = process_monitor
        self.bus = event_bus
        debug_log("AutomationEngine initialized", component="automation_engine")

    def run_workflow(
        self,
        workflow: WorkflowSpec,
        *,
        agent: Any = None,
    ) -> AutomationResult:
        debug_log(
            "Workflow execution started (placeholder)",
            component="automation_engine",
            data={"workflow": workflow.name, "tasks": [t.name for t in workflow.tasks]},
        )
        self.bus.emit(
            "automation.workflow_started",
            {"workflow": workflow.name, "tasks": [t.name for t in workflow.tasks]},
            source="automation_engine",
        )

        completed: list[str] = []

        for task in workflow.tasks:
            debug_log(
                "Executing task (placeholder)",
                component="automation_engine",
                data={"workflow": workflow.name, "task": task.name, "action": task.action},
            )
            self.bus.emit(
                "automation.task_started",
                {"workflow": workflow.name, "task": task.name, "action": task.action},
                source="automation_engine",
            )

            # Placeholder: simulate that tasks may request launching a process.
            if task.action == "launch_process":
                spec = ProcessSpec(
                    name=str(task.parameters.get("name") or task.name),
                    argv=list(task.parameters.get("argv") or []),
                    cwd=task.parameters.get("cwd"),
                    env=dict(task.parameters.get("env") or {}),
                )
                handle = self.process_monitor.launch_process(spec)
                _ = self.process_monitor.poll(handle)

                # Placeholder crash check.
                error = self.process_monitor.detect_crash(handle)
                if error is not None:
                    debug_log(
                        "Process crash detected during workflow",
                        component="automation_engine",
                        level="WARN",
                        data={"task": task.name, "pid": error.process.pid},
                    )
                    debug_result = debug_error(
                        error_data=_error_data_to_mapping(error),
                        agent=agent,
                        context={"workflow": workflow.name, "task": task.name},
                    )
                    self.bus.emit(
                        "automation.workflow_failed",
                        {"workflow": workflow.name, "task": task.name, "reason": "process_crash"},
                        source="automation_engine",
                    )
                    return AutomationResult(
                        status="failed",
                        workflow=workflow.name,
                        completed_tasks=completed,
                        failed_task=task.name,
                        debug_result=debug_result,
                        metadata={"reason": "process_crash"},
                    )

            # Placeholder: no real work performed.
            completed.append(task.name)
            self.bus.emit(
                "automation.task_finished",
                {"workflow": workflow.name, "task": task.name},
                source="automation_engine",
            )

        debug_log(
            "Workflow execution completed (placeholder)",
            component="automation_engine",
            data={"workflow": workflow.name, "completed": completed},
        )
        self.bus.emit(
            "automation.workflow_finished",
            {"workflow": workflow.name, "completed": completed},
            source="automation_engine",
        )
        return AutomationResult(
            status="ok",
            workflow=workflow.name,
            completed_tasks=completed,
            failed_task=None,
            debug_result=None,
        )


def _error_data_to_mapping(error: ErrorData) -> dict[str, Any]:
    return {
        "process": {
            "pid": error.process.pid,
            "name": error.process.spec.name,
            "argv": error.process.spec.argv,
            "cwd": error.process.spec.cwd,
        },
        "detected_at": error.detected_at.isoformat(),
        "error_type": error.error_type,
        "exit_code": error.exit_code,
        "message": error.message,
        "logs": [
            {"ts": line.ts.isoformat(), "source": line.source, "message": line.message}
            for line in error.logs
        ],
        "metadata": dict(error.metadata),
    }


DEFAULT_AUTOMATION_ENGINE = AutomationEngine()
