"""Shared data models for the AutoLink subsystem.

These dataclasses are the contracts spoken between DAI, AutoLink components
(AutoLD/AutoLCE/AutoLM/AutoLIP) and the execution engines (AutoOD/AutoClink).
Keep this module dependency-free and stable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AutoTask:
    """A unit of work flowing through AutoLink."""

    task_id: str
    intent: str
    payload: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Routing hints — interpreted by AutoLD.
    sensitivity: str = "normal"          # "low" | "normal" | "high"
    complexity: str = "normal"           # "low" | "normal" | "high"
    latency_budget_ms: Optional[int] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextBundle:
    """Assembled context handed to the executor.

    Built by AutoLCE from memory (AutoLM) plus a system_state stub.
    """

    task_id: str
    memory: List[Dict[str, Any]] = field(default_factory=list)
    system_state: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


@dataclass
class RouteDecision:
    """Decision produced by AutoLD about where to execute the task."""

    target: str                          # "AutoOD" | "AutoClink"
    reason: str = ""
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
