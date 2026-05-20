"""AL request/response envelopes and API types.

Spec references: §2 (DAIRequest/ALResponse), §3 (AL endpoints), §1.4
(PermissionQuery/PermissionAnswer projection).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..core.permissions import Action


class DAIRequestKind(str, Enum):
    READ = "read"
    INVOKE = "invoke"
    STREAM = "stream"
    WRITE = "write"
    ENUMERATE = "enumerate"


class DAIRequest(BaseModel):
    """Envelope for every outbound DAI → AL call (§2.1)."""

    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:12]}")
    session_id: str
    source_id: str
    kind: DAIRequestKind
    capability: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    payload_meta: Dict[str, Any] = Field(default_factory=dict)
    timeout_ms: Optional[int] = None
    idempotency_key: Optional[str] = None


class ALWarning(BaseModel):
    code: str
    summary: str


class ALResponse(BaseModel):
    """Envelope for every AL → DAI response (§2.2)."""

    request_id: str
    session_id: str
    source_id: str
    ok: bool
    data: Optional[Any] = None
    warnings: List[ALWarning] = Field(default_factory=list)
    error: Optional[Dict[str, Any]] = None
    health: str
    latency_ms: int = 0
    pulse_seq: Optional[int] = None
    rule_chain: List[str] = Field(default_factory=list)


class RegisterSourceRequest(BaseModel):
    kind: str
    label: str
    description: str = ""
    capabilities: List[str] = Field(default_factory=list)
    vault_key_ref: Optional[str] = None
    endpoint: Dict[str, Any] = Field(default_factory=dict)
    quota: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    scope_class: str = "user"
    pulse_policy: str = "on_health_change"


class RegisterVaultEntryRequest(BaseModel):
    secret_value: str
    owner_scope: str = "user"
    rotates_at: Optional[datetime] = None


class RotateVaultEntryRequest(BaseModel):
    new_secret: Optional[str] = None


class ScopeRuleDraft(BaseModel):
    source_selector: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Action]
    constraints: Dict[str, Any] = Field(default_factory=dict)


class RegisterScopeRequest(BaseModel):
    class_: str = Field(alias="class", default="user")
    rules: List[ScopeRuleDraft] = Field(default_factory=list)
    parent: Optional[str] = None
    ttl_sec: Optional[int] = None

    model_config = {"populate_by_name": True}


class EvaluatePermissionRequest(BaseModel):
    session_id: str
    source_id: str
    action: Action
    capability: Optional[str] = None
    payload_meta: Dict[str, Any] = Field(default_factory=dict)


class ChipDraft(BaseModel):
    topic: str
    payload: Dict[str, Any]
    source_id: Optional[str] = None
    pinned: bool = False
    ttl_sec: Optional[int] = None


class StatusProjection(BaseModel):
    session_id: str
    session_state: str
    source_count: int
    healthy_sources: int
    active_scopes: List[str]
    active_sources: List[str]
    pulse_seq: int
    quota_pressure: Dict[str, int] = Field(default_factory=dict)
