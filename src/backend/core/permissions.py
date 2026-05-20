"""Scope, permissions, and policy engine.

Implements:
  §1.3 Scope system (composition by intersection)
  §1.4 Permission model (first-deny-wins, five-layer decision order)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .errors import make_error


class ScopeClass(str, Enum):
    SYSTEM = "system"
    INFRA = "infra"
    USER = "user"
    SESSION = "session"
    EPHEMERAL = "ephemeral"


class Action(str, Enum):
    READ = "read"
    INVOKE = "invoke"
    STREAM = "stream"
    WRITE = "write"
    ENUMERATE = "enumerate"


class SourceSelector(BaseModel):
    ids: Optional[List[str]] = None
    kinds: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class ScopeConstraints(BaseModel):
    max_calls: Optional[int] = None
    max_tokens: Optional[int] = None
    ttl_sec: Optional[int] = None
    allowed_capabilities: Optional[List[str]] = None


class ScopeRule(BaseModel):
    rule_id: str = Field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:10]}")
    source_selector: SourceSelector = Field(default_factory=SourceSelector)
    actions: List[Action]
    constraints: ScopeConstraints = Field(default_factory=ScopeConstraints)

    def selector_matches(self, *, source_id: str, kind: str, tags: List[str]) -> bool:
        sel = self.source_selector
        if sel.ids is not None and source_id not in sel.ids:
            return False
        if sel.kinds is not None and kind not in sel.kinds:
            return False
        if sel.tags is not None and not any(t in tags for t in sel.tags):
            return False
        return True


class Scope(BaseModel):
    scope_id: str = Field(default_factory=lambda: f"scope_{uuid.uuid4().hex[:10]}")
    class_: ScopeClass = Field(alias="class")
    rules: List[ScopeRule] = Field(default_factory=list)
    parent: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}


class PermissionQuery(BaseModel):
    session_id: str
    source_id: str
    action: Action
    capability: Optional[str] = None
    payload_meta: Dict[str, Any] = Field(default_factory=dict)


class PermissionAnswer(BaseModel):
    allowed: bool
    reasons: List[str] = Field(default_factory=list)
    rule_chain: List[str] = Field(default_factory=list)


_SYSTEM_DENY_POLICIES = [
    {
        "name": "actuator_consent",
        "applies_when": lambda *, kind, action, payload_meta: (
            kind == "Device.Actuator"
            and action == Action.INVOKE
            and not payload_meta.get("user_consent")
        ),
        "reason": "system policy: invoke on Device.Actuator requires user_consent",
    },
]


class ScopeRegistry:
    """In-memory registry of scopes. Scopes compose by intersection along
    the parent chain (§1.3)."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._scopes: Dict[str, Scope] = {}

    def register(self, scope: Scope) -> Scope:
        with self._lock:
            self._scopes[scope.scope_id] = scope
            return scope

    def get(self, scope_id: str) -> Scope:
        with self._lock:
            scope = self._scopes.get(scope_id)
            if scope is None:
                raise make_error("ErrScopeForbidden", f"Unknown scope: {scope_id}")
            return scope

    def chain(self, scope_ids: List[str]) -> List[Scope]:
        """Resolve a scope chain leaf → root, skipping expired scopes."""
        with self._lock:
            resolved: List[Scope] = []
            now = datetime.now(timezone.utc)
            for sid in scope_ids:
                scope = self._scopes.get(sid)
                if scope is None:
                    raise make_error("ErrScopeForbidden", f"Unknown scope in chain: {sid}")
                if scope.expires_at and scope.expires_at < now:
                    continue
                resolved.append(scope)
            return resolved


class PermissionEngine:
    """Evaluates PermissionQuery by composing system + scope rules.

    Decision order (first-deny-wins, §1.4):
      1. System policy
      2. User policy (derived from scope_chain entries of class USER/INFRA/SYSTEM)
      3. Session scope
      4. Source-local policy (consulted by the caller)
      5. Quota / health veto (consulted by the caller)
    """

    def __init__(self, scopes: ScopeRegistry) -> None:
        self._scopes = scopes

    def evaluate(
        self,
        *,
        query: PermissionQuery,
        scope_chain_ids: List[str],
        source_kind: str,
        source_tags: List[str],
    ) -> PermissionAnswer:
        reasons: List[str] = []
        rule_chain: List[str] = []

        # Layer 1 — system policy.
        for policy in _SYSTEM_DENY_POLICIES:
            if policy["applies_when"](
                kind=source_kind,
                action=query.action,
                payload_meta=query.payload_meta,
            ):
                return PermissionAnswer(
                    allowed=False,
                    reasons=[policy["reason"]],
                    rule_chain=[f"system:{policy['name']}"],
                )

        # Layer 2 + 3 — user/session scope rules. First-deny-wins.
        chain = self._scopes.chain(scope_chain_ids)
        if not chain:
            return PermissionAnswer(
                allowed=False,
                reasons=["no active scopes in session chain"],
                rule_chain=[],
            )

        any_rule_selected = False
        for scope in chain:
            for rule in scope.rules:
                if not rule.selector_matches(
                    source_id=query.source_id,
                    kind=source_kind,
                    tags=source_tags,
                ):
                    continue
                any_rule_selected = True
                if query.action not in rule.actions:
                    return PermissionAnswer(
                        allowed=False,
                        reasons=[
                            f"scope {scope.scope_id} selects source but denies action={query.action.value}"
                        ],
                        rule_chain=[f"{scope.scope_id}:{rule.rule_id}"],
                    )
                allowed_caps = rule.constraints.allowed_capabilities
                if (
                    allowed_caps is not None
                    and query.capability is not None
                    and query.capability not in allowed_caps
                ):
                    return PermissionAnswer(
                        allowed=False,
                        reasons=[
                            f"scope {scope.scope_id} forbids capability={query.capability}"
                        ],
                        rule_chain=[f"{scope.scope_id}:{rule.rule_id}"],
                    )
                rule_chain.append(f"{scope.scope_id}:{rule.rule_id}")

        # An empty selector (no ids/kinds/tags) matches every source. If no rule
        # selected our source, deny.
        if not any_rule_selected:
            return PermissionAnswer(
                allowed=False,
                reasons=["no scope in session chain grants this source"],
                rule_chain=[],
            )

        return PermissionAnswer(
            allowed=True,
            reasons=reasons or ["allowed by session scope chain"],
            rule_chain=rule_chain,
        )
