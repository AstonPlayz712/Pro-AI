"""Task system similar to VS Code tasks (placeholder).

TaskRunner supports:
- register_task()
- run_task()
- cancel_task()

Tasks are executed in background threads (placeholder). Cancellation is best-effort.
The runner emits events on start/finish/error via the provided EventBus.
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from uuid import uuid4

from core.debug_log import debug_log
from core.event_bus import EventBus, DEFAULT_EVENT_BUS


TaskFn = Callable[..., Any]


@dataclass(slots=True)
class TaskRecord:
    """Internal record for a running or completed task."""

    id: str
    name: str
    status: str
    future: Optional[Future] = None
    cancel_requested: bool = False
    result: Any = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TaskRunner:
    """Register and execute tasks with event emission."""

    def __init__(self, *, event_bus: EventBus = DEFAULT_EVENT_BUS, max_workers: int = 4) -> None:
        self._tasks: dict[str, TaskFn] = {}
        self._records: dict[str, TaskRecord] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._bus = event_bus
        debug_log("TaskRunner initialized", component="task_runner", data={"max_workers": max_workers})

    def register_task(self, name: str, fn: TaskFn) -> None:
        self._tasks[name] = fn
        debug_log("Task registered", component="task_runner", data={"name": name})

    def run_task(self, name: str, **kwargs: Any) -> str:
        if name not in self._tasks:
            raise KeyError(f"Task not registered: {name}")

        task_id = str(uuid4())
        record = TaskRecord(id=task_id, name=name, status="running", metadata={"kwargs_keys": list(kwargs.keys())})
        self._records[task_id] = record

        self._bus.publish(
            "task.started",
            {"task_id": task_id, "name": name, "kwargs": {k: "<omitted>" for k in kwargs.keys()}},
            source="task_runner",
        )
        self._bus.publish(
            "task.start",
            {"task_id": task_id, "name": name},
            source="task_runner",
        )

        debug_log(
            "Task started",
            component="task_runner",
            data={"task_id": task_id, "name": name},
        )

        def _wrapped() -> Any:
            if record.cancel_requested:
                record.status = "cancelled"
                raise RuntimeError("Task cancelled before execution")

            return self._tasks[name](**kwargs)

        future = self._executor.submit(_wrapped)
        record.future = future

        def _done_callback(f: Future) -> None:
            if record.cancel_requested and record.status != "cancelled":
                record.status = "cancelled"

            try:
                record.result = f.result()
                if record.status != "cancelled":
                    record.status = "ok"
                self._bus.publish(
                    "task.finished",
                    {"task_id": task_id, "name": name, "status": record.status},
                    source="task_runner",
                )
                self._bus.publish(
                    "task.finish",
                    {"task_id": task_id, "name": name, "status": record.status},
                    source="task_runner",
                )
                debug_log(
                    "Task finished",
                    component="task_runner",
                    data={"task_id": task_id, "name": name, "status": record.status},
                )
            except Exception as exc:  # noqa: BLE001
                record.status = "error"
                record.error = str(exc)
                self._bus.publish(
                    "task.error",
                    {"task_id": task_id, "name": name, "error": record.error},
                    source="task_runner",
                )
                self._bus.publish(
                    "task.errored",
                    {"task_id": task_id, "name": name, "error": record.error},
                    source="task_runner",
                )
                debug_log(
                    "Task errored",
                    component="task_runner",
                    level="WARN",
                    data={"task_id": task_id, "name": name, "error": record.error},
                )

        future.add_done_callback(_done_callback)
        return task_id

    def cancel_task(self, task_id: str) -> bool:
        record = self._records.get(task_id)
        if record is None:
            return False

        record.cancel_requested = True
        self._bus.publish("task.cancel_requested", {"task_id": task_id, "name": record.name}, source="task_runner")
        debug_log(
            "Cancel requested",
            component="task_runner",
            data={"task_id": task_id, "name": record.name},
        )

        if record.future is not None:
            record.future.cancel()
        return True

    def get_record(self, task_id: str) -> Optional[TaskRecord]:
        return self._records.get(task_id)


DEFAULT_TASK_RUNNER = TaskRunner()
