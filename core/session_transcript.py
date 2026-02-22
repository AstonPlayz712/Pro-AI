"""Append-only session transcript.

The transcript is the backend analog of a console/log panel: it records an
append-only stream of structured entries such as:
- events
- errors
- mode changes
- task results
- insight outputs

This is intentionally in-memory and bounded only by process lifetime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from core.debug_log import debug_log


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class TranscriptEntry:
    """Single transcript record."""

    ts: datetime
    kind: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)


class SessionTranscript:
    """In-memory append-only transcript."""

    def __init__(self) -> None:
        self._entries: list[TranscriptEntry] = []
        debug_log("SessionTranscript initialized", component="session_transcript")

    def append(self, kind: str, message: str, data: Optional[dict[str, Any]] = None) -> TranscriptEntry:
        entry = TranscriptEntry(ts=utc_now(), kind=kind, message=message, data=dict(data or {}))
        self._entries.append(entry)
        debug_log(
            "Transcript appended",
            component="session_transcript",
            data={"kind": kind, "message": message, "data_keys": list(entry.data.keys())},
        )
        return entry

    def get_recent(self, limit: int = 50) -> list[TranscriptEntry]:
        return self._entries[-max(0, limit) :]

    def get_all(self) -> list[TranscriptEntry]:
        return list(self._entries)

    def clear(self) -> None:
        count = len(self._entries)
        self._entries.clear()
        debug_log("Transcript cleared", component="session_transcript", data={"count": count})


DEFAULT_SESSION_TRANSCRIPT = SessionTranscript()
