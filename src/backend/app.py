"""FastAPI application factory for Auto (DAI + AutoLink).

Composes ALManager + DAIManager and exposes their routers under `/al/*` and
`/dai/*`. A default session, scope, and source are bootstrapped at startup
so callers can exercise the system without admin pre-flight steps.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .al.manager import ALManager
from .al.models import (
    RegisterScopeRequest,
    RegisterSourceRequest,
    ScopeRuleDraft,
)
from .al.router import build_al_router
from .core.permissions import Action
from .core.session import IdentityMode
from .dai.manager import DAIManager
from .dai.router import build_dai_router


def create_app() -> FastAPI:
    """Build the Auto FastAPI app with AL + DAI wired up."""

    al = ALManager()
    dai = DAIManager(al)

    # -- Bootstrap: a permissive default scope + a session that uses it ----
    # The default scope grants read/invoke/stream/enumerate on every source.
    # Admins can register narrower scopes via POST /al/scopes; the default
    # session can be replaced or augmented by attaching new scopes.
    default_scope = al.register_scope(
        RegisterScopeRequest(
            **{"class": "user"},
            rules=[
                ScopeRuleDraft(
                    source_selector={},
                    actions=[
                        Action.READ,
                        Action.INVOKE,
                        Action.STREAM,
                        Action.WRITE,
                        Action.ENUMERATE,
                    ],
                    constraints={},
                ),
            ],
        )
    )
    default_session = al.sessions.create(
        identity_mode=IdentityMode.LOCAL_USER,
        scope_chain=[default_scope.scope_id],
    )

    # -- App -------------------------------------------------------------

    app = FastAPI(
        title="Auto Backend",
        description="DAI + AutoLink (AL) — per logic spec §1–§9",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.al = al
    app.state.dai = dai
    app.state.default_session_id = default_session.session_id
    app.state.default_scope_id = default_scope.scope_id

    def get_al() -> ALManager:
        return al

    def get_dai() -> DAIManager:
        return dai

    app.include_router(build_al_router(get_al))
    app.include_router(build_dai_router(get_dai))

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "healthy",
            "default_session_id": default_session.session_id,
            "default_scope_id": default_scope.scope_id,
        }

    @app.get("/")
    def root() -> dict:
        return {
            "service": "auto",
            "endpoints": {
                "al": [
                    "POST /al/sources",
                    "GET /al/sources",
                    "POST /al/scopes",
                    "POST /al/scopes/evaluate",
                    "GET /al/status",
                    "POST /al/api-keys",
                    "POST /al/api-keys/{ref}/rotate",
                    "GET /al/context",
                    "POST /al/context/chip",
                ],
                "dai": [
                    "POST /dai/message",
                    "GET /dai/state",
                    "POST /dai/goal",
                    "PATCH /dai/goal",
                    "POST /dai/subtask",
                    "PATCH /dai/subtask",
                    "GET /dai/context-map",
                ],
            },
            "default_session_id": default_session.session_id,
        }

    return app
