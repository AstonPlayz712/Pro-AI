"""Context fabric: chips and pulses.

Implements §1.9 (Context Chip) and §1.10 (Pulse).
Chip rules:
  - Pinning: pinned chips survive TTL expiry.
  - TTL: expired chips are not returned in context maps.
  - Redaction: chip payload may be scrubbed of vault refs.
  - Conflict: two chips with the same (topic, source_id) conflict — the
    newer one wins; the older one is marked superseded.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class PulseKind(str, Enum):
    HEALTH_CHANGE = "health_change"
    CONTENT_CHANGE = "content_change"
    CHIP_ADDED = "chip_added"
    CHIP_EXPIRED = "chip_expired"
    CHIP_SUPERSEDED = "chip_superseded"
    QUOTA_PRESSURE = "quota_pressure"
    SCOPE_CHANGE = "scope_change"
    SOURCE_REGISTERED = "source_registered"
    SOURCE_REMOVED = "source_removed"


class Pulse(BaseModel):
    """Ordered, per-session event (§1.10)."""

    pulse_id: str = Field(default_factory=lambda: f"pls_{uuid.uuid4().hex[:12]}")
    session_id: str
    seq: int
    kind: PulseKind
    source_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    emitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChipOrigin(str, Enum):
    DAI = "dai"
    AL = "al"
    SOURCE = "source"


class ContextChip(BaseModel):
    """A small, typed, named context fragment (§1.9)."""

    chip_id: str = Field(default_factory=lambda: f"chp_{uuid.uuid4().hex[:12]}")
    session_id: str
    topic: str
    source_id: Optional[str] = None
    origin: ChipOrigin = ChipOrigin.DAI
    payload: Dict[str, Any] = Field(default_factory=dict)
    pinned: bool = False
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    superseded_by: Optional[str] = None
    redacted: bool = False


_VAULT_REF_RE = re.compile(r"\bvault_[A-Za-z0-9]{4,}\b")


def _redact_value(value: Any) -> Tuple[Any, bool]:
    """Scrub vault refs + obvious secrets from a payload value. Returns (new, changed)."""
    changed = False
    if isinstance(value, str):
        new = _VAULT_REF_RE.sub("[redacted:vault_ref]", value)
        if new != value:
            changed = True
        return new, changed
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for k, v in value.items():
            if k in {"secret", "secret_value", "api_key", "authorization", "auth"}:
                out[k] = "[redacted]"
                changed = True
                continue
            nv, c = _redact_value(v)
            out[k] = nv
            changed = changed or c
        return out, changed
    if isinstance(value, list):
        new_list = []
        for item in value:
            nv, c = _redact_value(item)
            new_list.append(nv)
            changed = changed or c
        return new_list, changed
    return value, False


class ContextFabric:
    """Session-scoped chip store + pulse stream.

    Operations are ordered per session; every pulse carries a monotonically
    increasing `seq` sourced from SessionManager.touch().
    """

    def __init__(self, session_manager) -> None:
        self._sessions = session_manager
        self._lock = RLock()
        self._chips: Dict[str, ContextChip] = {}
        self._pulses: Dict[str, List[Pulse]] = {}

    def emit(
        self,
        *,
        session_id: str,
        kind: PulseKind,
        source_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Pulse:
        with self._lock:
            seq = self._sessions.touch(session_id)
            pulse = Pulse(
                session_id=session_id,
                seq=seq,
                kind=kind,
                source_id=source_id,
                payload=dict(payload or {}),
            )
            self._pulses.setdefault(session_id, []).append(pulse)
            return pulse

    def pulses(
        self,
        session_id: str,
        *,
        since_seq: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Pulse]:
        with self._lock:
            stream = list(self._pulses.get(session_id, []))
            if since_seq is not None:
                stream = [p for p in stream if p.seq > since_seq]
            if limit is not None:
                stream = stream[-limit:]
            return stream

    def add_chip(
        self,
        *,
        session_id: str,
        topic: str,
        payload: Dict[str, Any],
        source_id: Optional[str] = None,
        origin: ChipOrigin = ChipOrigin.DAI,
        pinned: bool = False,
        ttl_sec: Optional[int] = None,
        redact: bool = True,
    ) -> ContextChip:
        with self._lock:
            clean, changed = _redact_value(payload) if redact else (payload, False)
            expires_at = None
            if ttl_sec is not None:
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_sec)
            chip = ContextChip(
                session_id=session_id,
                topic=topic,
                source_id=source_id,
                origin=origin,
                payload=clean if isinstance(clean, dict) else {"value": clean},
                pinned=pinned,
                expires_at=expires_at,
                redacted=bool(changed),
            )
            for other in self._chips.values():
                if (
                    other.session_id == session_id
                    and other.topic == topic
                    and other.source_id == source_id
                    and other.superseded_by is None
                    and other.chip_id != chip.chip_id
                ):
                    other.superseded_by = chip.chip_id
                    self.emit(
                        session_id=session_id,
                        kind=PulseKind.CHIP_SUPERSEDED,
                        source_id=source_id,
                        payload={"old_chip_id": other.chip_id, "new_chip_id": chip.chip_id},
                    )
            self._chips[chip.chip_id] = chip
            self.emit(
                session_id=session_id,
                kind=PulseKind.CHIP_ADDED,
                source_id=source_id,
                payload={"chip_id": chip.chip_id, "topic": topic, "pinned": pinned},
            )
            return chip

    def get_chip(self, chip_id: str) -> Optional[ContextChip]:
        with self._lock:
            return self._chips.get(chip_id)

    def pin(self, chip_id: str, pinned: bool = True) -> Optional[ContextChip]:
        with self._lock:
            chip = self._chips.get(chip_id)
            if chip is None:
                return None
            chip.pinned = pinned
            return chip

    def drop_chip(self, chip_id: str) -> Optional[ContextChip]:
        with self._lock:
            return self._chips.pop(chip_id, None)

    def active_chips(self, session_id: str) -> List[ContextChip]:
        with self._lock:
            now = datetime.now(timezone.utc)
            out: List[ContextChip] = []
            for chip in self._chips.values():
                if chip.session_id != session_id:
                    continue
                if chip.superseded_by is not None:
                    continue
                if (
                    chip.expires_at is not None
                    and not chip.pinned
                    and chip.expires_at < now
                ):
                    continue
                out.append(chip)
            return out

    def sweep_expired(self, session_id: str) -> List[str]:
        with self._lock:
            now = datetime.now(timezone.utc)
            expired: List[str] = []
            for chip in self._chips.values():
                if chip.session_id != session_id:
                    continue
                if chip.pinned or chip.superseded_by is not None:
                    continue
                if chip.expires_at is not None and chip.expires_at < now:
                    expired.append(chip.chip_id)
            for cid in expired:
                chip = self._chips[cid]
                self.emit(
                    session_id=session_id,
                    kind=PulseKind.CHIP_EXPIRED,
                    source_id=chip.source_id,
                    payload={"chip_id": cid, "topic": chip.topic},
                )
            return expired

    def context_map(self, session_id: str) -> Dict[str, Any]:
        chips = self.active_chips(session_id)
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for chip in chips:
            grouped.setdefault(chip.topic, []).append(
                {
                    "chip_id": chip.chip_id,
                    "source_id": chip.source_id,
                    "origin": chip.origin.value,
                    "pinned": chip.pinned,
                    "redacted": chip.redacted,
                    "expires_at": chip.expires_at.isoformat() if chip.expires_at else None,
                    "payload": chip.payload,
                }
            )
        return {"session_id": session_id, "topics": grouped}
