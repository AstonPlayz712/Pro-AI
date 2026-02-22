"""Natural-language command interpreter.

This module parses text like:
- "Switch to Debugging Mode"
- "Use Automation Mode"
- "Analyse this in Insight Mode"

and maps them to structured command objects plus mode updates.

Parsing is intentionally heuristic and conservative (placeholder). It should be
replaced/augmented later with richer NL understanding and command routing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from core.debug_log import debug_log
from core.mode_manager import Mode, ModeManager, DEFAULT_MODE_MANAGER


@dataclass(frozen=True, slots=True)
class Command:
    """Structured interpretation of an incoming command string."""

    raw: str
    kind: str
    mode: Optional[Mode]
    confidence: float
    matched_phrase: str


_MODE_SYNONYMS: list[tuple[Mode, list[str]]] = [
    (Mode.SMART, ["smart", "assistant", "help", "normal"]),
    (Mode.DEBUG, ["debug", "debugging", "diagnostic", "troubleshoot", "troubleshooting"]),
    (Mode.AUTOMATION, ["automation", "automate", "workflow", "run tasks", "execute"]),
    (Mode.INSIGHT, ["insight", "analysis", "analyse", "analytics", "summarize", "summary"]),
]

_SWITCH_VERBS = [
    "switch",
    "set",
    "use",
    "go",
    "enter",
    "change",
    "turn on",
    "enable",
]


def _find_mode(text: str) -> tuple[Optional[Mode], str, float]:
    lowered = text.lower()

    for mode, keys in _MODE_SYNONYMS:
        for key in keys:
            if key in lowered:
                score = 0.7
                if "mode" in lowered:
                    score += 0.2
                if any(v in lowered for v in _SWITCH_VERBS):
                    score += 0.1
                return mode, key, min(1.0, score)

    return None, "", 0.0


def interpret(
    text: str,
    *,
    mode_manager: ModeManager = DEFAULT_MODE_MANAGER,
    apply: bool = True,
) -> Command:
    """Interpret a text command.

    Args:
        text: Natural-language command.
        mode_manager: Mode manager instance to target.
        apply: If True, apply mode changes via mode_manager.set_mode.

    Returns:
        A structured Command.
    """

    raw = text
    cleaned = text.strip()

    if not cleaned:
        debug_log("Empty command received", component="command_interpreter")
        return Command(raw=raw, kind="noop", mode=None, confidence=1.0, matched_phrase="")

    mode, phrase, confidence = _find_mode(cleaned)

    wants_switch = bool(
        re.search(r"\b(" + "|".join(re.escape(v) for v in _SWITCH_VERBS) + r")\b", cleaned.lower())
    ) or ("mode" in cleaned.lower())

    if mode is None:
        debug_log(
            "Command did not match any mode",
            component="command_interpreter",
            data={"raw": raw},
        )
        return Command(raw=raw, kind="unknown", mode=None, confidence=0.0, matched_phrase="")

    kind = "set_mode" if wants_switch else "mention_mode"

    debug_log(
        "Command parsed",
        component="command_interpreter",
        data={"raw": raw, "kind": kind, "mode": mode.value, "confidence": confidence},
    )

    if apply and kind == "set_mode":
        mode_manager.set_mode(mode, reason=f"command: {raw}")

    return Command(raw=raw, kind=kind, mode=mode, confidence=confidence, matched_phrase=phrase)
