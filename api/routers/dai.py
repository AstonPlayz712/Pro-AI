"""DAI HTTP surface.

Reserved for future DAI-specific endpoints (system map, evolution log,
agent introspection). For now `/dai/run` mirrors `/autolink/run` so the UI
has a stable contract to build against.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dai.interface import make_something, run_intelligence_task

router = APIRouter(prefix="/dai", tags=["dai"])


class RunRequest(BaseModel):
    intent: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    user_id: str
    session_id: Optional[str] = None
    sensitivity: str = "normal"
    complexity: str = "normal"
    latency_budget_ms: Optional[int] = None


class MakeRequest(BaseModel):
    goal: str
    mode: Optional[str] = None
    user_id: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/run")
def run(req: RunRequest) -> Dict[str, Any]:
    # TODO: split into DAI-specific orchestration once DAI grows distinct
    # verbs (design, evolve, plan). For now we pass through to AutoLink.
    try:
        return run_intelligence_task(
            intent=req.intent,
            payload=req.payload,
            user_id=req.user_id,
            session_id=req.session_id,
            sensitivity=req.sensitivity,
            complexity=req.complexity,
            latency_budget_ms=req.latency_budget_ms,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/make")
def make(req: MakeRequest) -> Dict[str, Any]:
    try:
        return make_something(req.model_dump(exclude_none=False))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/system-map")
def system_map() -> Dict[str, Any]:
    # TODO: load dai/system_map.yaml and return parsed tree.
    return {
        "status": "stub",
        "todo": "load dai/system_map.yaml",
        "modules": [
            {"name": "AutoLink", "children": ["AutoLD", "AutoLCE", "AutoLM", "AutoLIP"]},
            {"name": "Engines", "children": ["AutoOD", "AutoClink"]},
            {"name": "DAI", "children": ["Director", "Registry"]},
        ],
    }


@router.get("/evolution-log")
def evolution_log() -> Dict[str, Any]:
    # TODO: tail DAI evolution log from registry.
    return {
        "status": "stub",
        "todo": "read evolution log from registry",
        "entries": [],
    }
