"""Structured error model for the Auto backend.

Every error carries a machine-readable code, a short summary, optional
details, and never contains a secret. Error codes and HTTP mappings follow
the logic spec (§6).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AutoError(BaseModel):
    """Structured error envelope."""

    code: str
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)
    retriable: bool = False
    source_id: Optional[str] = None
    request_id: Optional[str] = None
    rule_chain: Optional[List[str]] = None


class AutoException(Exception):
    """Raised internally to surface an AutoError at the API boundary."""

    def __init__(self, error: AutoError, *, http_status: int = 400) -> None:
        super().__init__(error.summary)
        self.error = error
        self.http_status = http_status


# Canonical error codes — spec §6.1 and §6.2.
AL_CODES = {
    "ErrSessionUnknown": (404, False),
    "ErrScopeForbidden": (403, False),
    "ErrPolicyDenied": (403, False),
    "ErrQuotaExceeded": (429, True),
    "ErrSourceUnknown": (404, False),
    "ErrSourceUnreachable": (503, True),
    "ErrSourceDegraded": (200, True),  # warning, not a hard failure
    "ErrSourceRevoked": (410, False),
    "ErrVaultRefUnknown": (404, False),
    "ErrVaultRevoked": (410, False),
    "ErrCapabilityUnsupported": (400, False),
    "ErrSchemaInvalid": (400, False),
    "ErrTimeout": (504, True),
    "ErrIngestorBackpressure": (503, True),
    "ErrSourceDuplicate": (409, False),
    "ErrPulseOrder": (500, False),
}

DAI_CODES = {
    "ErrDAIStateLocked": (409, True),
    "ErrGoalConflict": (409, False),
    "ErrSubtaskCycle": (400, False),
    "ErrSubtaskUnknown": (404, False),
    "ErrModeVetoed": (403, False),
    "ErrChipExpired": (410, False),
    "ErrChipConflict": (409, False),
    "ErrLowConfidence": (412, False),
}

ALL_CODES = {**AL_CODES, **DAI_CODES}


def make_error(
    code: str,
    summary: str,
    *,
    details: Optional[Dict[str, Any]] = None,
    source_id: Optional[str] = None,
    request_id: Optional[str] = None,
    rule_chain: Optional[List[str]] = None,
) -> AutoException:
    """Build an AutoException with HTTP status + retriability inferred from code."""
    http_status, retriable = ALL_CODES.get(code, (400, False))
    err = AutoError(
        code=code,
        summary=summary,
        details=details or {},
        retriable=retriable,
        source_id=source_id,
        request_id=request_id,
        rule_chain=rule_chain,
    )
    return AutoException(err, http_status=http_status)
