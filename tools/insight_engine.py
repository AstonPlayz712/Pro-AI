"""Insight engine placeholders.

Insight Mode focuses on analysis and summarization.

This module intentionally avoids real log parsing or ML-based analytics for now.
It provides structured inputs/outputs and debug hooks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from core.debug_log import debug_log
from core.event_bus import DEFAULT_EVENT_BUS


@dataclass(frozen=True, slots=True)
class InsightRequest:
    """Input to InsightEngine."""

    text: Optional[str] = None
    logs: Optional[list[str]] = None
    data: Optional[Mapping[str, Any]] = None
    goal: str = "summarize"


@dataclass(frozen=True, slots=True)
class InsightResult:
    """Structured analysis output (placeholder)."""

    status: str
    summary: str
    patterns: list[str]
    highlights: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


class InsightEngine:
    """Placeholder analysis engine."""

    def __init__(self) -> None:
        debug_log("InsightEngine initialized", component="insight_engine")

    def analyze(
        self,
        req: Optional[InsightRequest] = None,
        *,
        text: Optional[str] = None,
        logs: Optional[list[str]] = None,
        data: Optional[Mapping[str, Any]] = None,
        goal: str = "summarize",
    ) -> InsightResult:
        if req is None:
            req = InsightRequest(text=text, logs=logs, data=data, goal=goal)
        debug_log(
            "Insight analysis requested (placeholder)",
            component="insight_engine",
            data={
                "goal": req.goal,
                "has_text": bool(req.text),
                "has_logs": bool(req.logs),
                "has_data": bool(req.data),
            },
        )
        DEFAULT_EVENT_BUS.emit(
            "insight.requested",
            {"goal": req.goal, "has_text": bool(req.text), "has_logs": bool(req.logs), "has_data": bool(req.data)},
            source="insight_engine",
        )

        patterns: list[str] = []
        highlights: list[str] = []

        if req.logs:
            patterns.append("Log input provided (no parsing yet)")
            highlights.append(f"Log lines: {len(req.logs)}")
        if req.text:
            patterns.append("Text input provided")
            highlights.append(f"Text chars: {len(req.text)}")
        if req.data:
            patterns.append("Structured data provided")
            highlights.append(f"Data keys: {list(req.data.keys())[:10]}")

        if not patterns:
            patterns.append("No inputs provided")

        summary = "Placeholder insight summary."
        result = InsightResult(
            status="ok",
            summary=summary,
            patterns=patterns,
            highlights=highlights,
            metadata={"goal": req.goal},
        )
        DEFAULT_EVENT_BUS.emit(
            "insight.produced",
            {"status": result.status, "patterns": len(result.patterns), "highlights": len(result.highlights)},
            source="insight_engine",
        )
        return result


DEFAULT_INSIGHT_ENGINE = InsightEngine()
