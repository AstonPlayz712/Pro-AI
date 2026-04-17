"""AutoLink HTTP surface.

Thin adapter: the request body becomes an AutoTask via DAI's
`run_intelligence_task`. AutoLink / DAI core logic is untouched.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dai.interface import run_intelligence_task

router = APIRouter(prefix="/autolink", tags=["autolink"])


class RunRequest(BaseModel):
    intent: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    user_id: str
    session_id: Optional[str] = None
    sensitivity: str = "normal"
    complexity: str = "normal"
    latency_budget_ms: Optional[int] = None


@router.get("/ping")
def ping() -> Dict[str, str]:
    return {"status": "ok", "service": "autolink"}


@router.post("/run")
def run(req: RunRequest) -> Dict[str, Any]:
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
