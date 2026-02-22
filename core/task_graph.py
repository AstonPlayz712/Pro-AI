"""Task graph scaffolding.

Provides placeholder structures for modeling:
- dependencies
- parallel execution groups
- conditional tasks
- retry/timeout policies

Execution is NOT implemented yet; TaskRunner remains the execution backend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Placeholder retry policy."""

    max_retries: int = 0
    backoff_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class TimeoutPolicy:
    """Placeholder timeout policy."""

    timeout_seconds: Optional[float] = None


@dataclass(slots=True)
class TaskNode:
    """Single task node in a graph."""

    name: str
    task_name: str
    depends_on: list[str] = field(default_factory=list)
    condition: Optional[str] = None
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    timeout: TimeoutPolicy = field(default_factory=TimeoutPolicy)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TaskGraph:
    """Collection of task nodes."""

    nodes: dict[str, TaskNode] = field(default_factory=dict)

    def add_node(self, node: TaskNode) -> None:
        self.nodes[node.name] = node

    def get_node(self, name: str) -> Optional[TaskNode]:
        return self.nodes.get(name)

    def list_nodes(self) -> list[TaskNode]:
        return [self.nodes[name] for name in sorted(self.nodes.keys())]

    def validate(self) -> list[str]:
        """Return a list of validation errors (placeholder)."""

        errors: list[str] = []
        for node in self.nodes.values():
            for dep in node.depends_on:
                if dep not in self.nodes:
                    errors.append(f"Node '{node.name}' depends on missing '{dep}'")
        return errors
