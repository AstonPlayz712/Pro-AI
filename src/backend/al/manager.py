"""ALManager — orchestrates the DAI→AL→Source request lifecycle.

Spec references:
  §2 (DAIRequest/ALResponse)
  §4 (Request lifecycle — 10 steps)
  §5 (Pulse lifecycle)
  §1.6 (Quota leases)
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..core.api_keys import KeyBroker, Vault, VaultEntryDraft, VaultEntryView
from ..core.audit import AuditLog, DecisionKind
from ..core.context import ChipOrigin, ContextChip, ContextFabric, PulseKind
from ..core.errors import AutoException, make_error
from ..core.health import CALLABLE_STATES, HealthMonitor, HealthState, WARNING_STATES
from ..core.permissions import (
    Action,
    PermissionEngine,
    PermissionQuery,
    Scope,
    ScopeClass,
    ScopeConstraints,
    ScopeRegistry,
    ScopeRule,
    SourceSelector as PermSourceSelector,
)
from ..core.session import SessionManager
from ..core.sources import (
    EndpointDescriptor,
    QuotaDescriptor,
    Source,
    SourceDraft,
    SourceRegistry,
    SourceView,
    source_to_view,
)
from .models import (
    ALResponse,
    ALWarning,
    DAIRequest,
    DAIRequestKind,
    EvaluatePermissionRequest,
    RegisterScopeRequest,
    RegisterSourceRequest,
    RegisterVaultEntryRequest,
    RotateVaultEntryRequest,
    StatusProjection,
)


_KIND_TO_ACTION = {
    DAIRequestKind.READ: Action.READ,
    DAIRequestKind.INVOKE: Action.INVOKE,
    DAIRequestKind.STREAM: Action.STREAM,
    DAIRequestKind.WRITE: Action.WRITE,
    DAIRequestKind.ENUMERATE: Action.ENUMERATE,
}


TransportFn = Callable[
    [Source, Action, Optional[str], Dict[str, Any], Optional[str]],
    Tuple[Any, List[ALWarning]],
]


def _default_transport(
    source: Source,
    action: Action,
    capability: Optional[str],
    payload: Dict[str, Any],
    secret: Optional[str],
) -> Tuple[Any, List[ALWarning]]:
    """Deterministic, side-effect-free stand-in for real I/O."""
    return (
        {
            "source_id": source.source_id,
            "kind": source.kind,
            "action": action.value,
            "capability": capability,
            "payload_echo": payload,
            "authenticated": secret is not None,
        },
        [],
    )


class _QuotaTracker:
    """Tracks calls-per-minute per source with a sliding window."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._calls: Dict[str, List[datetime]] = {}

    def acquire(self, source: Source) -> None:
        limit = source.quota.max_calls_per_minute
        with self._lock:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(seconds=60)
            hist = [t for t in self._calls.get(source.source_id, []) if t >= window_start]
            if limit is not None and len(hist) >= limit:
                raise make_error(
                    "ErrQuotaExceeded",
                    f"Source {source.source_id} exceeded {limit} calls/min",
                    source_id=source.source_id,
                )
            hist.append(now)
            self._calls[source.source_id] = hist

    def pressure(self, source_id: str) -> int:
        with self._lock:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(seconds=60)
            hist = [t for t in self._calls.get(source_id, []) if t >= window_start]
            self._calls[source_id] = hist
            return len(hist)


class ALManager:
    """The environment layer DAI talks to."""

    def __init__(self, *, transport: TransportFn = _default_transport) -> None:
        self.sources = SourceRegistry()
        self.vault = Vault()
        self.broker = KeyBroker(self.vault)
        self.scopes = ScopeRegistry()
        self.permissions = PermissionEngine(self.scopes)
        self.health = HealthMonitor()
        self.sessions = SessionManager()
        self.fabric = ContextFabric(self.sessions)
        self.audit = AuditLog()
        self._quota = _QuotaTracker()
        self._transport = transport

        self.health.add_listener(self._on_health_change)

    # -- Source admin ----------------------------------------------------

    def register_source(self, req: RegisterSourceRequest) -> SourceView:
        draft = SourceDraft(
            kind=req.kind,
            label=req.label,
            description=req.description,
            capabilities=list(req.capabilities),
            vault_key_ref=req.vault_key_ref,
            endpoint=EndpointDescriptor(**req.endpoint),
            quota=QuotaDescriptor(**req.quota),
            tags=list(req.tags),
            scope_class=req.scope_class,
            pulse_policy=req.pulse_policy,
        )
        src = self.sources.register(draft, vault_key_ref=req.vault_key_ref)
        self.audit.log(
            DecisionKind.SCOPE_CHANGE,
            actor="admin",
            source_id=src.source_id,
            details={"event": "source_registered", "kind": src.kind, "label": src.label},
        )
        for sess in self.sessions.list():
            if sess.state.value == "ACTIVE":
                self.fabric.emit(
                    session_id=sess.session_id,
                    kind=PulseKind.SOURCE_REGISTERED,
                    source_id=src.source_id,
                    payload={"kind": src.kind, "label": src.label},
                )
        return source_to_view(src)

    def list_sources(self) -> List[SourceView]:
        return [source_to_view(s) for s in self.sources.list()]

    def get_source(self, source_id: str) -> SourceView:
        return source_to_view(self.sources.get(source_id))

    # -- Scope admin -----------------------------------------------------

    def register_scope(self, req: RegisterScopeRequest) -> Scope:
        rules = [
            ScopeRule(
                source_selector=PermSourceSelector(**r.source_selector),
                actions=list(r.actions),
                constraints=ScopeConstraints(**r.constraints),
            )
            for r in req.rules
        ]
        expires = None
        if req.ttl_sec is not None:
            expires = datetime.now(timezone.utc) + timedelta(seconds=req.ttl_sec)
        scope = Scope(
            **{"class": ScopeClass(req.class_)},
            rules=rules,
            parent=req.parent,
            expires_at=expires,
        )
        self.scopes.register(scope)
        self.audit.log(
            DecisionKind.SCOPE_CHANGE,
            actor="admin",
            details={
                "scope_id": scope.scope_id,
                "class": scope.class_.value,
                "rule_count": len(rules),
            },
        )
        return scope

    def list_scopes(self) -> List[Scope]:
        with self.scopes._lock:  # type: ignore[attr-defined]
            return list(self.scopes._scopes.values())  # type: ignore[attr-defined]

    def evaluate_permission(self, req: EvaluatePermissionRequest):
        sess = self.sessions.get(req.session_id)
        src = self.sources.get(req.source_id)
        answer = self.permissions.evaluate(
            query=PermissionQuery(
                session_id=req.session_id,
                source_id=req.source_id,
                action=req.action,
                capability=req.capability,
                payload_meta=req.payload_meta,
            ),
            scope_chain_ids=sess.scope_chain,
            source_kind=src.kind,
            source_tags=list(src.tags),
        )
        self.audit.log(
            DecisionKind.PERMISSION_CHECK,
            actor="al",
            session_id=req.session_id,
            source_id=req.source_id,
            action=req.action.value,
            allowed=answer.allowed,
            reasons=list(answer.reasons),
            rule_chain=list(answer.rule_chain),
        )
        return answer

    # -- Vault admin -----------------------------------------------------

    def register_vault_entry(self, req: RegisterVaultEntryRequest) -> VaultEntryView:
        view = self.vault.register(
            VaultEntryDraft(
                secret_value=req.secret_value,
                owner_scope=req.owner_scope,
                rotates_at=req.rotates_at,
            )
        )
        self.audit.log(
            DecisionKind.VAULT_ACTION,
            actor="admin",
            details={"event": "register", "vault_key_ref": view.vault_key_ref},
        )
        return view

    def rotate_vault_entry(self, vault_key_ref: str, req: RotateVaultEntryRequest) -> VaultEntryView:
        view = self.vault.rotate(vault_key_ref, new_secret=req.new_secret)
        self.audit.log(
            DecisionKind.VAULT_ACTION,
            actor="admin",
            details={"event": "rotate", "vault_key_ref": view.vault_key_ref},
        )
        return view

    def list_vault_entries(self) -> List[VaultEntryView]:
        return self.vault.list()

    # -- Context / status -----------------------------------------------

    def context_map(self, session_id: str) -> Dict[str, Any]:
        self.sessions.get(session_id)
        self.fabric.sweep_expired(session_id)
        return self.fabric.context_map(session_id)

    def add_chip(
        self,
        *,
        session_id: str,
        topic: str,
        payload: Dict[str, Any],
        source_id: Optional[str] = None,
        pinned: bool = False,
        ttl_sec: Optional[int] = None,
        origin: ChipOrigin = ChipOrigin.DAI,
    ) -> ContextChip:
        self.sessions.get(session_id)
        return self.fabric.add_chip(
            session_id=session_id,
            topic=topic,
            payload=payload,
            source_id=source_id,
            pinned=pinned,
            ttl_sec=ttl_sec,
            origin=origin,
        )

    def status(self, session_id: str) -> StatusProjection:
        sess = self.sessions.get(session_id)
        all_sources = list(self.sources)
        healthy = sum(
            1 for s in all_sources if self.health.state(s.source_id) == HealthState.HEALTHY
        )
        pressure = {s.source_id: self._quota.pressure(s.source_id) for s in all_sources}
        return StatusProjection(
            session_id=sess.session_id,
            session_state=sess.state.value,
            source_count=len(all_sources),
            healthy_sources=healthy,
            active_scopes=list(sess.scope_chain),
            active_sources=list(sess.active_sources),
            pulse_seq=sess.pulse_seq,
            quota_pressure=pressure,
        )

    # -- The 10-step DAI→AL request lifecycle ---------------------------

    def handle_request(self, req: DAIRequest) -> ALResponse:
        """Full request lifecycle (§4 step 1 → step 10)."""
        request_id = req.request_id
        started = time.perf_counter()

        # Step 1 — Session check.
        try:
            sess = self.sessions.require_active(req.session_id)
        except AutoException as exc:
            return self._fail(req, exc, health="UNKNOWN", started=started)

        # Step 2 — Source lookup.
        try:
            src = self.sources.get(req.source_id)
        except AutoException as exc:
            return self._fail(req, exc, health="UNKNOWN", started=started)

        current_health = self.health.state(req.source_id)

        # Step 3 — Terminal health gate.
        if current_health in (HealthState.REVOKED, HealthState.DISABLED):
            err = make_error(
                "ErrSourceRevoked" if current_health == HealthState.REVOKED else "ErrPolicyDenied",
                f"Source {req.source_id} is {current_health.value}",
                source_id=req.source_id,
                request_id=request_id,
            )
            return self._fail(req, err, health=current_health.value, started=started)

        # Step 4 — Permission check.
        action = _KIND_TO_ACTION[req.kind]
        answer = self.permissions.evaluate(
            query=PermissionQuery(
                session_id=req.session_id,
                source_id=req.source_id,
                action=action,
                capability=req.capability,
                payload_meta=req.payload_meta,
            ),
            scope_chain_ids=sess.scope_chain,
            source_kind=src.kind,
            source_tags=list(src.tags),
        )
        self.audit.log(
            DecisionKind.PERMISSION_CHECK,
            actor="al",
            session_id=req.session_id,
            source_id=req.source_id,
            action=action.value,
            allowed=answer.allowed,
            reasons=list(answer.reasons),
            rule_chain=list(answer.rule_chain),
            details={"request_id": request_id},
        )
        if not answer.allowed:
            err = make_error(
                "ErrPolicyDenied",
                "; ".join(answer.reasons) or "denied by scope chain",
                source_id=req.source_id,
                request_id=request_id,
                rule_chain=list(answer.rule_chain),
            )
            return self._fail(req, err, health=current_health.value, started=started)

        # Step 5 — Capability check (source-local).
        if req.capability is not None and req.capability not in src.capabilities:
            err = make_error(
                "ErrCapabilityUnsupported",
                f"Source {req.source_id} does not support capability={req.capability}",
                source_id=req.source_id,
                request_id=request_id,
            )
            return self._fail(req, err, health=current_health.value, started=started)

        # Step 6 — Quota lease.
        try:
            self._quota.acquire(src)
            self.audit.log(
                DecisionKind.QUOTA_LEASE,
                actor="al",
                session_id=req.session_id,
                source_id=req.source_id,
                details={"request_id": request_id, "action": action.value},
            )
        except AutoException as exc:
            self.fabric.emit(
                session_id=req.session_id,
                kind=PulseKind.QUOTA_PRESSURE,
                source_id=req.source_id,
                payload={"reason": "exceeded"},
            )
            return self._fail(req, exc, health=current_health.value, started=started)

        # Step 7 — Non-callable health states (UNREACHABLE).
        if current_health == HealthState.UNREACHABLE:
            err = make_error(
                "ErrSourceUnreachable",
                f"Source {req.source_id} is {current_health.value}",
                source_id=req.source_id,
                request_id=request_id,
            )
            return self._fail(req, err, health=current_health.value, started=started)

        # Step 8 — Broker call (vault closure + transport).
        warnings: List[ALWarning] = []
        if current_health in WARNING_STATES:
            warnings.append(
                ALWarning(code="ErrSourceDegraded", summary=f"Source {req.source_id} is DEGRADED")
            )

        try:
            data, transport_warnings = self.broker.call_with_secret(
                src.auth_ref,
                lambda secret: self._transport(src, action, req.capability, req.payload, secret),
            )
            warnings.extend(transport_warnings)
            self.health.record_ok(req.source_id)
        except AutoException as exc:
            if exc.error.code == "ErrVaultRevoked":
                self.health.record_auth_failure(req.source_id)
            else:
                self.health.record_degraded(req.source_id, reason=exc.error.code)
            return self._fail(
                req, exc, health=self.health.state(req.source_id).value, started=started
            )
        except TimeoutError:
            self.health.record_timeout(req.source_id)
            err = make_error(
                "ErrTimeout",
                f"Source {req.source_id} timed out",
                source_id=req.source_id,
                request_id=request_id,
            )
            return self._fail(
                req, err, health=self.health.state(req.source_id).value, started=started
            )
        except Exception as exc:  # pragma: no cover — defensive catch-all
            self.health.record_degraded(req.source_id, reason="transport_error")
            err = make_error(
                "ErrSourceUnreachable",
                f"Transport error: {exc}",
                source_id=req.source_id,
                request_id=request_id,
            )
            return self._fail(
                req, err, health=self.health.state(req.source_id).value, started=started
            )

        # Step 9 — Bookkeeping.
        self.sources.touch(req.source_id)
        final_health = self.health.state(req.source_id)
        pulse_seq = sess.pulse_seq
        self.audit.log(
            DecisionKind.OUTBOUND_CALL,
            actor="al",
            session_id=req.session_id,
            source_id=req.source_id,
            action=action.value,
            allowed=True,
            reasons=list(answer.reasons),
            rule_chain=list(answer.rule_chain),
            details={
                "request_id": request_id,
                "health_before": current_health.value,
                "health_after": final_health.value,
                "warnings": [w.code for w in warnings],
            },
        )

        # Step 10 — Build the ALResponse envelope.
        latency_ms = int((time.perf_counter() - started) * 1000)
        return ALResponse(
            request_id=request_id,
            session_id=req.session_id,
            source_id=req.source_id,
            ok=True,
            data=data,
            warnings=warnings,
            error=None,
            health=final_health.value,
            latency_ms=latency_ms,
            pulse_seq=pulse_seq,
            rule_chain=list(answer.rule_chain),
        )

    # -- Helpers ---------------------------------------------------------

    def _fail(
        self,
        req: DAIRequest,
        exc: AutoException,
        *,
        health: str,
        started: float,
    ) -> ALResponse:
        latency_ms = int((time.perf_counter() - started) * 1000)
        err = exc.error.model_dump()
        err.pop("secret_value", None)
        return ALResponse(
            request_id=req.request_id,
            session_id=req.session_id,
            source_id=req.source_id,
            ok=False,
            data=None,
            warnings=[],
            error=err,
            health=health,
            latency_ms=latency_ms,
            pulse_seq=None,
            rule_chain=exc.error.rule_chain or [],
        )

    def _on_health_change(self, source_id: str, old: HealthState, new: HealthState) -> None:
        try:
            self.sources.set_health(source_id, new.value)
        except AutoException:
            return
        self.audit.log(
            DecisionKind.HEALTH_TRANSITION,
            actor="al",
            source_id=source_id,
            details={"old": old.value, "new": new.value},
        )
        for sess in self.sessions.list():
            if sess.state.value != "ACTIVE":
                continue
            self.fabric.emit(
                session_id=sess.session_id,
                kind=PulseKind.HEALTH_CHANGE,
                source_id=source_id,
                payload={"old": old.value, "new": new.value},
            )
