"""Simple publish/subscribe event bus.

This module provides a lightweight in-process event mechanism so components can
emit structured events and other components can listen to them.

Notes:
- This is intentionally minimal (no persistence, no guarantees, no distributed bus).
- Handlers are called synchronously in publish order.
- `debug_log` is used for all event emissions.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from uuid import uuid4

from core.debug_log import debug_log


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class Event:
    """Structured event message."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "core"
    ts: datetime = field(default_factory=utc_now)


EventHandler = Callable[[Event], None]


@dataclass(slots=True)
class Subscription:
    """Subscription record."""

    id: str
    pattern: str
    handler: EventHandler
    once: bool = False


class EventBus:
    """In-process synchronous pub/sub."""

    def __init__(self) -> None:
        self._subs: dict[str, Subscription] = {}
        debug_log("EventBus initialized", component="event_bus")

    def subscribe(self, pattern: str, handler: EventHandler, *, once: bool = False) -> str:
        """Subscribe a handler to event name pattern (glob-style).

        Examples:
            pattern='task.*'
            pattern='mode.changed'
        """

        sub_id = str(uuid4())
        self._subs[sub_id] = Subscription(id=sub_id, pattern=pattern, handler=handler, once=once)
        debug_log(
            "Subscribed to events",
            component="event_bus",
            data={"id": sub_id, "pattern": pattern, "once": once},
        )
        return sub_id

    def unsubscribe(self, sub_id: str) -> bool:
        """Unsubscribe by subscription id."""

        existed = sub_id in self._subs
        if existed:
            sub = self._subs.pop(sub_id)
            debug_log(
                "Unsubscribed from events",
                component="event_bus",
                data={"id": sub_id, "pattern": sub.pattern},
            )
        return existed

    def publish(self, name: str, payload: Optional[dict[str, Any]] = None, *, source: str = "core") -> Event:
        """Publish an event and synchronously notify matching subscribers."""

        event = Event(name=name, payload=dict(payload or {}), source=source)
        debug_log(
            "Event emitted",
            component="event_bus",
            data={"name": event.name, "source": event.source, "payload_keys": list(event.payload.keys())},
        )

        to_remove: list[str] = []
        for sub_id, sub in list(self._subs.items()):
            if fnmatch.fnmatch(event.name, sub.pattern):
                try:
                    sub.handler(event)
                except Exception as exc:  # noqa: BLE001
                    debug_log(
                        "Event handler raised (ignored)",
                        component="event_bus",
                        level="WARN",
                        data={"id": sub_id, "pattern": sub.pattern, "error": str(exc), "event": event.name},
                    )
                if sub.once:
                    to_remove.append(sub_id)

        for sub_id in to_remove:
            self.unsubscribe(sub_id)

        return event

    def emit(self, event_name: str, payload: Optional[dict[str, Any]] = None, *, source: str = "core") -> Event:
        """Emit an event.

        This is an alias for publish() to match the runtime API.
        """

        return self.publish(event_name, payload, source=source)


DEFAULT_EVENT_BUS = EventBus()
