"""Lightweight debug logging used across backend modules.

This project intentionally avoids heavy logging dependencies at the scaffold stage.
`debug_log` provides consistent, structured console logs that can later be routed to
files, UI panels, or observability backends.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping, Optional


def _json_default(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # type: ignore[no-any-return]
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def debug_log(
    message: str,
    *,
    component: str = "core",
    level: str = "INFO",
    data: Optional[Mapping[str, Any]] = None,
    stream: Any = None,
) -> None:
    """Emit a structured debug line.

    Args:
        message: Human-readable message.
        component: Subsystem name (e.g., mode_manager, process_monitor).
        level: Log level label.
        data: Optional structured payload.
        stream: Optional override for output stream.
    """

    output_stream = stream if stream is not None else sys.stdout
    payload: MutableMapping[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "level": level,
        "component": component,
        "msg": message,
    }
    if data:
        payload["data"] = dict(data)

    output_stream.write(json.dumps(payload, default=_json_default, ensure_ascii=False) + "\n")
    output_stream.flush()
