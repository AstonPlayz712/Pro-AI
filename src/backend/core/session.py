"""Session records and lifecycle.

Implements §1.8: Session = handle DAI uses to act inside AL, plus the state
machine INIT → ACTIVE → SUSPENDED ↔ ACTIVE → CLOSED/EXPIRED.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import RLock
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .errors import make_error


class SessionState(str, Enum):
    INIT = "INIT"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class IdentityMode(str, Enum):
    """DAI-visible identity mode — informational, does not grant privilege."""

    ANONYMOUS = "anonymous"
    LOCAL_USER = "local_user"
    SERVICE = "service"


_ALLOWED_SESSION_TRANSITIONS: Dict[SessionState, List[SessionState]] = {
    SessionState.INIT: [SessionState.ACTIVE, SessionState.CLOSED, SessionState.EXPIRED],
    SessionState.ACTIVE: [SessionState.SUSPENDED, SessionState.CLOSED, SessionState.EXPIRED],
    SessionState.SUSPENDED: [SessionState.ACTIVE, SessionState.CLOSED, SessionState.EXPIRED],
    SessionState.CLOSED: [],
    SessionState.EXPIRED: [],
}


def is_valid_session_transition(current: SessionState, target: SessionState) -> bool:
    if current == target:
        return True
    return target in _ALLOWED_SESSION_TRANSITIONS.get(current, [])


class Session(BaseModel):
    """Session record (§1.8)."""

    session_id: str = Field(default_factory=lambda: f"ses_{uuid.uuid4().hex[:12]}")
    user_id: Optional[str] = None
    identity_mode: IdentityMode = IdentityMode.ANONYMOUS
    scope_chain: List[str] = Field(default_factory=list)
    active_sources: List[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    state: SessionState = SessionState.INIT
    pulse_seq: int = 0


class SessionManager:
    """In-memory session registry with lifecycle transitions."""

    def __init__(self, *, default_ttl_sec: int = 3600) -> None:
        self._lock = RLock()
        self._sessions: Dict[str, Session] = {}
        self._default_ttl_sec = default_ttl_sec

    def create(
        self,
        *,
        user_id: Optional[str] = None,
        identity_mode: IdentityMode = IdentityMode.ANONYMOUS,
        scope_chain: Optional[List[str]] = None,
        active_sources: Optional[List[str]] = None,
        ttl_sec: Optional[int] = None,
    ) -> Session:
        with self._lock:
            ttl = ttl_sec if ttl_sec is not None else self._default_ttl_sec
            now = datetime.now(timezone.utc)
            sess = Session(
                user_id=user_id,
                identity_mode=identity_mode,
                scope_chain=list(scope_chain or []),
                active_sources=list(active_sources or []),
                started_at=now,
                expires_at=now + timedelta(seconds=ttl),
                state=SessionState.INIT,
            )
            self._sessions[sess.session_id] = sess
            if sess.scope_chain:
                self._set_state(sess, SessionState.ACTIVE)
            return sess

    def get(self, session_id: str) -> Session:
        with self._lock:
            sess = self._sessions.get(session_id)
            if sess is None:
                raise make_error("ErrSessionUnknown", f"No such session: {session_id}")
            self._maybe_expire(sess)
            return sess

    def list(self) -> List[Session]:
        with self._lock:
            now = datetime.now(timezone.utc)
            for s in list(self._sessions.values()):
                self._maybe_expire(s, now=now)
            return list(self._sessions.values())

    def touch(self, session_id: str) -> int:
        with self._lock:
            sess = self.get(session_id)
            sess.pulse_seq += 1
            return sess.pulse_seq

    def attach_scope(self, session_id: str, scope_id: str) -> Session:
        with self._lock:
            sess = self.get(session_id)
            if scope_id not in sess.scope_chain:
                sess.scope_chain.append(scope_id)
            if sess.state == SessionState.INIT:
                self._set_state(sess, SessionState.ACTIVE)
            return sess

    def attach_source(self, session_id: str, source_id: str) -> Session:
        with self._lock:
            sess = self.get(session_id)
            if source_id not in sess.active_sources:
                sess.active_sources.append(source_id)
            return sess

    def detach_source(self, session_id: str, source_id: str) -> Session:
        with self._lock:
            sess = self.get(session_id)
            sess.active_sources = [s for s in sess.active_sources if s != source_id]
            return sess

    def suspend(self, session_id: str) -> Session:
        with self._lock:
            sess = self.get(session_id)
            self._set_state(sess, SessionState.SUSPENDED)
            return sess

    def resume(self, session_id: str) -> Session:
        with self._lock:
            sess = self.get(session_id)
            self._set_state(sess, SessionState.ACTIVE)
            return sess

    def close(self, session_id: str) -> Session:
        with self._lock:
            sess = self.get(session_id)
            self._set_state(sess, SessionState.CLOSED)
            return sess

    def _set_state(self, sess: Session, target: SessionState) -> None:
        if not is_valid_session_transition(sess.state, target):
            raise make_error(
                "ErrDAIStateLocked",
                f"Cannot transition session {sess.session_id} from {sess.state.value} to {target.value}",
            )
        sess.state = target

    def _maybe_expire(self, sess: Session, *, now: Optional[datetime] = None) -> None:
        if sess.state in (SessionState.CLOSED, SessionState.EXPIRED):
            return
        now = now or datetime.now(timezone.utc)
        if sess.expires_at is not None and sess.expires_at < now:
            sess.state = SessionState.EXPIRED

    def require_active(self, session_id: str) -> Session:
        sess = self.get(session_id)
        if sess.state != SessionState.ACTIVE:
            raise make_error(
                "ErrDAIStateLocked",
                f"Session {sess.session_id} is {sess.state.value}, not ACTIVE",
            )
        return sess
