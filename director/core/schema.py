"""
schema.py — JSON-serializable dataclasses for all DAI request/response contracts.

Every specialist must accept a subclass of DAIRequest and return a subclass of
DAIResponse.  The top-level DAI layer always wraps results in DAIResponse.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ProblemDomain(str, Enum):
    ITS_MAC_BOOT   = "its_mac_boot"
    ITS_WINDOWS    = "its_windows"
    NETWORK        = "network"
    UNKNOWN        = "unknown"


class Severity(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    LOW    = "low"     # < 0.40
    MEDIUM = "medium"  # 0.40 – 0.74
    HIGH   = "high"    # >= 0.75


# ---------------------------------------------------------------------------
# Base request / response
# ---------------------------------------------------------------------------

@dataclass
class DAIRequest:
    """Top-level request fed into the Director-AI."""
    request_id:    str        = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp:     float      = field(default_factory=time.time)
    raw_text:      str        = ""
    image_paths:   list[str]  = field(default_factory=list)
    # Additional key/value context (e.g. device model, OS version)
    context:       dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DAIResponse:
    """Top-level response returned by the Director-AI."""
    request_id:    str
    timestamp:     float      = field(default_factory=time.time)
    domain:        ProblemDomain = ProblemDomain.UNKNOWN
    confidence:    float      = 0.0
    confidence_lvl: ConfidenceLevel = ConfidenceLevel.LOW
    summary:       str        = ""
    actions:       list[str]  = field(default_factory=list)
    specialist_output: dict[str, Any] = field(default_factory=dict)
    error:         str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["domain"] = self.domain.value
        d["confidence_lvl"] = self.confidence_lvl.value
        return d

    @staticmethod
    def confidence_to_level(score: float) -> ConfidenceLevel:
        if score >= 0.75:
            return ConfidenceLevel.HIGH
        if score >= 0.40:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW


# ---------------------------------------------------------------------------
# ITS — Mac Boot specialist
# ---------------------------------------------------------------------------

@dataclass
class ITSRequest(DAIRequest):
    """Specialist request for Mac boot diagnostics."""
    device_model:  str = ""   # e.g. "MacBook Pro 2010"
    symptom_tags:  list[str] = field(default_factory=list)
    vision_text:   str = ""   # OCR/vision output from boot screen image


@dataclass
class ITSFinding:
    pattern_id:   str
    pattern_name: str
    matched:      bool
    score:        float
    evidence:     list[str] = field(default_factory=list)


@dataclass
class ITSResponse(DAIResponse):
    """Specialist response from Mac boot diagnostics."""
    severity:      Severity          = Severity.LOW
    root_cause:    str               = ""
    findings:      list[ITSFinding]  = field(default_factory=list)
    repair_steps:  list[str]         = field(default_factory=list)
    parts_needed:  list[str]         = field(default_factory=list)
    references:    list[str]         = field(default_factory=list)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["severity"] = self.severity.value
        d["findings"] = [asdict(f) for f in self.findings]
        return d
