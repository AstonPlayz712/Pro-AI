"""
router.py — Maps an incoming DAIRequest to the correct specialist agent.

Routing is keyword + context based.  Each entry in ROUTE_TABLE holds a set of
trigger keywords and the factory function that builds the matching specialist.
The router scores every entry against the request and returns the highest-
scoring specialist (or None if nothing clears the minimum threshold).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

from director.core.schema import DAIRequest, ProblemDomain

if TYPE_CHECKING:
    from director.specialists.base import BaseSpecialist

logger = logging.getLogger(__name__)

# Minimum keyword score required to consider a route a match
MIN_SCORE_THRESHOLD = 0.10


@dataclass
class RouteEntry:
    domain:   ProblemDomain
    keywords: list[str]        # matched against combined request text
    factory:  Callable[[], "BaseSpecialist"]
    priority: int = 0          # tie-breaker; higher wins


def _score(text: str, keywords: list[str]) -> float:
    """Return fraction of keywords present in `text` (case-insensitive)."""
    if not keywords:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw.lower()) + r"\b", text_lower))
    return hits / len(keywords)


class Router:
    """
    Matches a DAIRequest to a specialist.

    Usage
    -----
    router = Router()
    router.register(entry)
    specialist = router.route(request)
    """

    def __init__(self) -> None:
        self._table: list[RouteEntry] = []

    def register(self, entry: RouteEntry) -> None:
        self._table.append(entry)
        logger.debug("Registered route: domain=%s priority=%d", entry.domain, entry.priority)

    def route(self, request: DAIRequest) -> "BaseSpecialist | None":
        """Return the best-matching specialist instance, or None."""
        combined = " ".join([
            request.raw_text,
            request.context.get("device_model", ""),
            request.context.get("symptom_tags", ""),
            request.context.get("vision_text", ""),
        ])

        best_entry: RouteEntry | None = None
        best_score = 0.0

        for entry in self._table:
            score = _score(combined, entry.keywords)
            logger.debug(
                "Route score domain=%s score=%.3f", entry.domain, score
            )
            if score < MIN_SCORE_THRESHOLD:
                continue
            if score > best_score or (
                score == best_score
                and best_entry is not None
                and entry.priority > best_entry.priority
            ):
                best_score = score
                best_entry = entry

        if best_entry is None:
            logger.warning("No route matched for request_id=%s", request.request_id)
            return None

        logger.info(
            "Routing to domain=%s score=%.3f request_id=%s",
            best_entry.domain, best_score, request.request_id,
        )
        specialist = best_entry.factory()
        specialist.matched_score = best_score
        return specialist


# ---------------------------------------------------------------------------
# Default route table — import specialists lazily to avoid circular imports
# ---------------------------------------------------------------------------

def build_default_router() -> Router:
    router = Router()

    # ITS — Mac Boot
    def _its_mac_boot_factory():
        from director.specialists.its_mac_boot.agent import ITSMacBootAgent
        return ITSMacBootAgent()

    router.register(RouteEntry(
        domain=ProblemDomain.ITS_MAC_BOOT,
        keywords=[
            "macbook", "mac", "boot", "startup", "kernel panic",
            "sata", "hard drive", "hdd", "no bootable device",
            "folder with question mark", "prohibitory symbol",
            "2010", "spinning wheel", "safe mode",
        ],
        factory=_its_mac_boot_factory,
        priority=10,
    ))

    return router
