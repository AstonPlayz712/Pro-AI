"""FastAPI routes for the AL surface (§3 AL endpoints)."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException

from ..core.api_keys import VaultEntryView
from ..core.context import ContextChip
from ..core.errors import AutoException
from ..core.permissions import Scope
from ..core.sources import SourceView
from .manager import ALManager
from .models import (
    ChipDraft,
    EvaluatePermissionRequest,
    RegisterScopeRequest,
    RegisterSourceRequest,
    RegisterVaultEntryRequest,
    RotateVaultEntryRequest,
    StatusProjection,
)


def _session_header(x_session_id: str = Header(..., alias="X-Session-Id")) -> str:
    return x_session_id


def build_al_router(get_manager) -> APIRouter:
    router = APIRouter(prefix="/al", tags=["autolink"])

    def _exc(exc: AutoException) -> HTTPException:
        return HTTPException(status_code=exc.http_status, detail=exc.error.model_dump())

    @router.post("/sources", response_model=SourceView)
    def register_source(
        req: RegisterSourceRequest,
        mgr: ALManager = Depends(get_manager),
    ) -> SourceView:
        try:
            return mgr.register_source(req)
        except AutoException as exc:
            raise _exc(exc)

    @router.get("/sources", response_model=List[SourceView])
    def list_sources(mgr: ALManager = Depends(get_manager)) -> List[SourceView]:
        return mgr.list_sources()

    @router.get("/sources/{source_id}", response_model=SourceView)
    def get_source(source_id: str, mgr: ALManager = Depends(get_manager)) -> SourceView:
        try:
            return mgr.get_source(source_id)
        except AutoException as exc:
            raise _exc(exc)

    @router.post("/scopes", response_model=Scope)
    def register_scope(
        req: RegisterScopeRequest,
        mgr: ALManager = Depends(get_manager),
    ) -> Scope:
        try:
            return mgr.register_scope(req)
        except AutoException as exc:
            raise _exc(exc)

    @router.get("/scopes", response_model=List[Scope])
    def list_scopes(mgr: ALManager = Depends(get_manager)) -> List[Scope]:
        return mgr.list_scopes()

    @router.post("/scopes/evaluate")
    def evaluate_scope(
        req: EvaluatePermissionRequest,
        mgr: ALManager = Depends(get_manager),
    ):
        try:
            return mgr.evaluate_permission(req)
        except AutoException as exc:
            raise _exc(exc)

    @router.get("/status", response_model=StatusProjection)
    def status(
        session_id: str = Depends(_session_header),
        mgr: ALManager = Depends(get_manager),
    ) -> StatusProjection:
        try:
            return mgr.status(session_id)
        except AutoException as exc:
            raise _exc(exc)

    @router.post("/api-keys", response_model=VaultEntryView)
    def register_api_key(
        req: RegisterVaultEntryRequest,
        mgr: ALManager = Depends(get_manager),
    ) -> VaultEntryView:
        try:
            return mgr.register_vault_entry(req)
        except AutoException as exc:
            raise _exc(exc)

    @router.get("/api-keys", response_model=List[VaultEntryView])
    def list_api_keys(mgr: ALManager = Depends(get_manager)) -> List[VaultEntryView]:
        return mgr.list_vault_entries()

    @router.post("/api-keys/{ref}/rotate", response_model=VaultEntryView)
    def rotate_api_key(
        ref: str,
        req: RotateVaultEntryRequest,
        mgr: ALManager = Depends(get_manager),
    ) -> VaultEntryView:
        try:
            return mgr.rotate_vault_entry(ref, req)
        except AutoException as exc:
            raise _exc(exc)

    @router.get("/context")
    def context(
        session_id: str = Depends(_session_header),
        mgr: ALManager = Depends(get_manager),
    ) -> Dict[str, Any]:
        try:
            return mgr.context_map(session_id)
        except AutoException as exc:
            raise _exc(exc)

    @router.post("/context/chip", response_model=ContextChip)
    def add_chip(
        req: ChipDraft,
        session_id: str = Depends(_session_header),
        mgr: ALManager = Depends(get_manager),
    ) -> ContextChip:
        try:
            return mgr.add_chip(
                session_id=session_id,
                topic=req.topic,
                payload=req.payload,
                source_id=req.source_id,
                pinned=req.pinned,
                ttl_sec=req.ttl_sec,
            )
        except AutoException as exc:
            raise _exc(exc)

    return router
