"""
ALRequest / ALResponse protocol.

Defines the typed message structures used for all communication between
DAI and the AutoLink (AL) layer.  DAI integrates chips by ID only —
no payload is ever copied into DAI state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


# ---------------------------------------------------------------------------
# Request side
# ---------------------------------------------------------------------------

RequestType = Literal["model", "search", "tool", "source", "pulse_subscribe"]


@dataclass
class DAIRequest:
    """
    A structured request emitted by DAI to AutoLink.

    Fields
    ------
    request_id          Unique identifier for this request (auto-generated
                        when not supplied).
    type                Category of AL capability being requested.
    payload             Opaque object forwarded verbatim to the target AL
                        capability.  DAI does not inspect or store the
                        payload after emission.
    reason              Human-readable explanation of why this request was
                        emitted; used for transparency and auditability.
    required_confidence Minimum confidence threshold (0.0 – 1.0) that DAI
                        requires the resulting chip(s) to carry before it
                        will act on them.
    """

    type: RequestType
    payload: Dict[str, Any]
    reason: str
    required_confidence: float
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "type": self.type,
            "payload": self.payload,
            "reason": self.reason,
            "required_confidence": self.required_confidence,
        }


# ---------------------------------------------------------------------------
# Chip returned in a response
# ---------------------------------------------------------------------------

@dataclass
class ResponseChip:
    """
    A context chip returned by AL inside an ALResponse.

    DAI stores only the chip_id as a reference — the payload stays inside
    the chip object and is never copied elsewhere.
    """

    chip_id: str
    source: str
    confidence: float    # 0.0 – 1.0
    ttl: float           # Unix epoch expiry; 0 means no expiry
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "chip_id": self.chip_id,
            "source": self.source,
            "confidence": self.confidence,
            "ttl": self.ttl,
            "payload": self.payload,
        }


# ---------------------------------------------------------------------------
# Error detail
# ---------------------------------------------------------------------------

@dataclass
class ALError:
    type: str
    message: str

    def to_dict(self) -> dict:
        return {"type": self.type, "message": self.message}


# ---------------------------------------------------------------------------
# Response side
# ---------------------------------------------------------------------------

ResponseStatus = Literal["success", "error"]


@dataclass
class ALResponse:
    """
    A structured response returned by AutoLink to DAI.

    Rules enforced by this structure
    ---------------------------------
    - ``chips`` carries the full chip objects; DAI must reference them by
      ``chip_id`` only and must not copy ``payload`` content into its own
      state.
    - TTL and confidence are preserved as-is from AL; DAI is responsible
      for checking them before acting.
    - When ``status == "error"`` the ``error`` field will be populated.
    """

    request_id: str
    status: ResponseStatus
    data: Dict[str, Any] = field(default_factory=dict)
    chips: List[ResponseChip] = field(default_factory=list)
    error: Optional[ALError] = None

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "status": self.status,
            "data": self.data,
            "chips": [c.to_dict() for c in self.chips],
            "error": self.error.to_dict() if self.error is not None else None,
        }

    # ------------------------------------------------------------------
    # Chip access helpers (enforce ID-only integration)
    # ------------------------------------------------------------------

    def get_chip_ids(self) -> List[str]:
        """Return the IDs of all chips in this response."""
        return [c.chip_id for c in self.chips]

    def get_chip_by_id(self, chip_id: str) -> Optional[ResponseChip]:
        """Look up a chip by its ID without copying it."""
        for chip in self.chips:
            if chip.chip_id == chip_id:
                return chip
        return None


__all__ = [
    "RequestType",
    "DAIRequest",
    "ResponseChip",
    "ALError",
    "ResponseStatus",
    "ALResponse",
]
