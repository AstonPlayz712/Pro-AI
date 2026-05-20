"""FastAPI routes for the DAI surface (§8 DAI endpoints)."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException

from ..core.errors import AutoException
from .manager import DAIManager
from .models import (
    DAIStateProjection,
    Goal,
    GoalDraftRequest,
    GoalTransitionRequest,
    MessageRequest,
    MessageResponse,
    Subtask,
    SubtaskDraftRequest,
    SubtaskTransitionRequest,
)


def _session_header(x_session_id: str = Header(..., alias="X-Session-Id")) -> str:
    return x_session_id


def build_dai_router(get_manager) -> APIRouter:
    router = APIRouter(prefix="/dai", tags=["dai"])

    def _exc(exc: AutoException) -> HTTPException:
        return HTTPException(status_code=exc.http_status, detail=exc.error.model_dump())

    @router.post("/message", response_model=MessageResponse)
    def message(
        req: MessageRequest,
        session_id: str = Depends(_session_header),
        mgr: DAIManager = Depends(get_manager),
    ) -> MessageResponse:
        try:
            return mgr.handle_message(session_id, req)
        except AutoException as exc:
            raise _exc(exc)

    @router.get("/state", response_model=DAIStateProjection)
    def state(
        session_id: str = Depends(_session_header),
        mgr: DAIManager = Depends(get_manager),
    ) -> DAIStateProjection:
        try:
            return mgr.project(session_id)
        except AutoException as exc:
            raise _exc(exc)

    @router.post("/goal", response_model=Goal)
    def create_goal(
        req: GoalDraftRequest,
        session_id: str = Depends(_session_header),
        mgr: DAIManager = Depends(get_manager),
    ) -> Goal:
        try:
            return mgr.draft_goal(session_id, req)
        except AutoException as exc:
            raise _exc(exc)

    @router.patch("/goal", response_model=Goal)
    def transition_goal(
        req: GoalTransitionRequest,
        session_id: str = Depends(_session_header),
        mgr: DAIManager = Depends(get_manager),
    ) -> Goal:
        try:
            return mgr.transition_goal(session_id, req)
        except AutoException as exc:
            raise _exc(exc)

    @router.post("/subtask", response_model=Subtask)
    def create_subtask(
        req: SubtaskDraftRequest,
        session_id: str = Depends(_session_header),
        mgr: DAIManager = Depends(get_manager),
    ) -> Subtask:
        try:
            return mgr.draft_subtask(session_id, req)
        except AutoException as exc:
            raise _exc(exc)

    @router.patch("/subtask", response_model=Subtask)
    def transition_subtask(
        req: SubtaskTransitionRequest,
        session_id: str = Depends(_session_header),
        mgr: DAIManager = Depends(get_manager),
    ) -> Subtask:
        try:
            return mgr.transition_subtask(session_id, req)
        except AutoException as exc:
            raise _exc(exc)

    @router.get("/context-map")
    def context_map(
        session_id: str = Depends(_session_header),
        mgr: DAIManager = Depends(get_manager),
    ) -> Dict[str, Any]:
        try:
            return mgr.context_map(session_id)
        except AutoException as exc:
            raise _exc(exc)

    return router
