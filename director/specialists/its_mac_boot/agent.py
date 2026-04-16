"""
agent.py — ITS.mac_boot specialist agent.

Diagnoses MacBook Pro 2010 boot failures, with a focus on SATA cable
and related hardware/software issues.

Decision flow
-------------
1. Collect all available text: raw_text + vision OCR + symptom_tags.
2. Score each pattern in patterns.json against the collected signals.
3. Select the highest-scoring pattern(s) above the threshold.
4. Optionally enrich findings with a web search for the top pattern.
5. Build and return an ITSResponse.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from director.core.schema import (
    DAIRequest,
    DAIResponse,
    ITSRequest,
    ITSResponse,
    ITSFinding,
    ProblemDomain,
    Severity,
    ConfidenceLevel,
)
from director.specialists.base import BaseSpecialist

logger = logging.getLogger(__name__)

PATTERNS_PATH = Path(__file__).parent / "patterns.json"
MATCH_THRESHOLD = 0.20   # minimum pattern score to include in findings
TOP_N_FINDINGS  = 3      # maximum findings to surface


class ITSMacBootAgent(BaseSpecialist):
    """
    Diagnostic specialist for MacBook Pro 2010 boot failures.

    Supported pattern categories (see patterns.json):
      P001 — SATA Cable Failure (question mark folder)
      P002 — Kernel Panic / AHCI I/O errors
      P003 — Prohibitory symbol / OS corruption
      P004 — Spinning globe / EFI fallback
      P005 — Clicking / grinding HDD (critical)
    """

    def __init__(self) -> None:
        self._patterns: list[dict[str, Any]] = self._load_patterns()

    # ------------------------------------------------------------------
    # BaseSpecialist interface
    # ------------------------------------------------------------------

    def run(self, request: DAIRequest) -> DAIResponse:
        try:
            # Normalise to ITSRequest if needed
            its_req = self._coerce(request)

            # Collect all signal text
            signal = self._build_signal(its_req)

            # Score patterns
            findings = self._score_patterns(signal)

            # Optionally enrich via web search
            top = findings[0] if findings else None
            references: list[str] = []
            if top and top.matched:
                references = self._web_enrich(top)

            # Build response
            return self._build_response(its_req, findings, references, top)

        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("ITSMacBootAgent.run failed: %s", exc)
            return DAIResponse(
                request_id=request.request_id,
                domain=ProblemDomain.ITS_MAC_BOOT,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_patterns() -> list[dict[str, Any]]:
        with open(PATTERNS_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        return data["patterns"]

    @staticmethod
    def _coerce(request: DAIRequest) -> ITSRequest:
        """Promote a generic DAIRequest to ITSRequest."""
        if isinstance(request, ITSRequest):
            return request
        return ITSRequest(
            request_id=request.request_id,
            timestamp=request.timestamp,
            raw_text=request.raw_text,
            image_paths=request.image_paths,
            context=request.context,
            device_model=request.context.get("device_model", ""),
            symptom_tags=request.context.get("symptom_tags", []),
            vision_text=request.context.get("vision_text", ""),
        )

    @staticmethod
    def _build_signal(req: ITSRequest) -> str:
        """Combine all text signals into a single lowercase string."""
        parts = [
            req.raw_text,
            req.vision_text,
            req.device_model,
            " ".join(req.symptom_tags),
            req.context.get("vision_text", ""),
        ]
        return " ".join(p for p in parts if p).lower()

    def _score_patterns(self, signal: str) -> list[ITSFinding]:
        """Score every pattern against the signal; return sorted findings."""
        findings: list[ITSFinding] = []

        for pat in self._patterns:
            kw_hits:     list[str] = []
            vis_hits:    list[str] = []

            for kw in pat.get("keywords", []):
                if re.search(r"\b" + re.escape(kw.lower()) + r"\b", signal):
                    kw_hits.append(kw)

            for vkw in pat.get("vision_keywords", []):
                if vkw.lower() in signal:
                    vis_hits.append(vkw)

            total_kw  = len(pat.get("keywords", [])) + len(pat.get("vision_keywords", []))
            total_hit = len(kw_hits) + len(vis_hits)

            raw_score = (total_hit / total_kw) if total_kw > 0 else 0.0
            # Weight by pattern-level confidence
            score = raw_score * pat.get("confidence_weight", 1.0)

            evidence = [f"keyword: {k}" for k in kw_hits] + [f"vision: {v}" for v in vis_hits]

            findings.append(ITSFinding(
                pattern_id=pat["id"],
                pattern_name=pat["name"],
                matched=score >= MATCH_THRESHOLD,
                score=round(score, 4),
                evidence=evidence,
            ))

        # Sort by score descending, return top N
        findings.sort(key=lambda f: f.score, reverse=True)
        return findings[:TOP_N_FINDINGS]

    def _web_enrich(self, finding: ITSFinding) -> list[str]:
        """Run a web search for the top finding and return reference URLs."""
        query = f"MacBook Pro 2010 {finding.pattern_name} fix repair"
        logger.debug("Web enrichment query: %s", query)
        try:
            resp = self.web_tool.search(query, max_results=3)
            return [r.url for r in resp.results if r.url]
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Web enrichment failed: %s", exc)
            return []

    def _build_response(
        self,
        req:        ITSRequest,
        findings:   list[ITSFinding],
        references: list[str],
        top:        ITSFinding | None,
    ) -> ITSResponse:
        """Assemble the final ITSResponse."""
        if not top or not top.matched:
            return ITSResponse(
                request_id=req.request_id,
                domain=ProblemDomain.ITS_MAC_BOOT,
                confidence=0.0,
                confidence_lvl=ConfidenceLevel.LOW,
                summary="No known failure pattern matched the provided symptoms.",
                actions=[
                    "Provide a screen image or more detailed symptom description.",
                    "Specify device model (13-inch or 15-inch).",
                ],
                findings=findings,
            )

        # Look up full pattern metadata
        pat = next((p for p in self._patterns if p["id"] == top.pattern_id), {})

        confidence = top.score
        severity   = Severity(pat.get("severity", "medium"))

        # Combine static references from pattern with live web results
        all_refs = list(dict.fromkeys(pat.get("references", []) + references))

        return ITSResponse(
            request_id=req.request_id,
            domain=ProblemDomain.ITS_MAC_BOOT,
            confidence=confidence,
            confidence_lvl=DAIResponse.confidence_to_level(confidence),
            summary=(
                f"Most likely cause: {top.pattern_name}. "
                f"Confidence: {confidence:.0%}. "
                f"Severity: {severity.value.upper()}."
            ),
            actions=pat.get("repair_steps", []),
            specialist_output={
                "pattern_id":   top.pattern_id,
                "pattern_name": top.pattern_name,
                "all_findings": [{"id": f.pattern_id, "name": f.pattern_name, "score": f.score}
                                 for f in findings],
            },
            severity=severity,
            root_cause=pat.get("root_cause", ""),
            findings=findings,
            repair_steps=pat.get("repair_steps", []),
            parts_needed=pat.get("parts_needed", []),
            references=all_refs,
        )
