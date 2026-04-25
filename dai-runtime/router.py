"""
DAI-Runtime · router.py
=======================

Connector-first routing engine for DAI Sub-AI calls.

Reads ``subai_registry.json`` and dispatches each task through the host's
external-connector surface. **Every connector is external.** DAI-Runtime
holds no API keys, no bearer tokens, no env-var-driven credentials.

Connector ids declared in ``connectors.json`` (WIP):

- ``perplexity``      — primary reasoning engine (via Perplexity Connector)
- ``claude_desktop``  — Claude Desktop / MCP bridge
- ``copilot``         — GitHub Copilot connector
- ``slack``           — Slack connector
- ``monday``          — Monday connector
- ``asana``           — Asana connector

To wire the runtime into your host, register a dispatcher once at startup:

    from dai_runtime.router import set_external_connector_dispatcher

    def my_dispatcher(connector_id: str, action: str, payload: dict) -> str:
        ...  # call the host's connector surface and return text

    set_external_connector_dispatcher(my_dispatcher)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .core import DAIRuntimeError  # noqa: WPS300

logger = logging.getLogger("dai_runtime.router")

_RUNTIME_DIR = Path(__file__).resolve().parent
_REGISTRY_PATH = _RUNTIME_DIR / "subai_registry.json"
_CONNECTORS_PATH = _RUNTIME_DIR / "connectors.json"


# ---------------------------------------------------------------------------
# External connector dispatcher (single chokepoint for ALL outbound calls)
# ---------------------------------------------------------------------------

ExternalDispatcher = Callable[[str, str, Dict[str, Any]], str]
_external_dispatcher: Optional[ExternalDispatcher] = None


def set_external_connector_dispatcher(dispatcher: ExternalDispatcher) -> None:
    """Register the host-supplied function that calls external connectors.

    Signature: ``dispatcher(connector_id, action, payload) -> str``.

    Until this is called, every outbound call raises ``DAIRuntimeError``
    so the missing wiring is visible rather than silent.
    """
    global _external_dispatcher
    _external_dispatcher = dispatcher


def _dispatch_external(connector_id: str, action: str, payload: Dict[str, Any]) -> str:
    if _external_dispatcher is None:
        raise DAIRuntimeError(
            f"External connector '{connector_id}' was invoked but no dispatcher is "
            "registered. Call set_external_connector_dispatcher() during bootstrap."
        )
    return _external_dispatcher(connector_id, action, payload)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def route_task(
    subai_name: str,
    task: str,
    *,
    registry: Optional[List[Dict[str, Any]]] = None,
    connectors: Optional[Dict[str, Any]] = None,
) -> str:
    """Route a task to the connector configured for the named Sub-AI.

    Returns the connector's textual response. Raises ``DAIRuntimeError``
    on routing or transport failure.
    """
    registry = registry if registry is not None else _read_json(_REGISTRY_PATH)
    connectors = connectors if connectors is not None else _read_json(_CONNECTORS_PATH)

    entry = next((s for s in registry if s["name"] == subai_name), None)
    if entry is None:
        raise DAIRuntimeError(f"Sub-AI '{subai_name}' not in registry.")

    connector_key = entry.get("connector", "perplexity").lower()
    connector_spec = connectors.get(connector_key)
    if connector_spec is None:
        raise DAIRuntimeError(
            f"Connector '{connector_key}' for Sub-AI '{subai_name}' is not defined "
            f"in connectors.json."
        )

    handler = _HANDLERS.get(connector_key)
    if handler is None:
        raise DAIRuntimeError(f"No router handler for connector '{connector_key}'.")

    logger.info("route_task → %s via %s", subai_name, connector_key)
    return handler(entry=entry, task=task, connector_spec=connector_spec)


# ---------------------------------------------------------------------------
# Connector handlers — all delegate to the dispatcher
# ---------------------------------------------------------------------------

def _handle_perplexity(*, entry: Dict[str, Any], task: str, connector_spec: Dict[str, Any]) -> str:
    system_prompt = entry.get("system_prompt") or ""
    payload: Dict[str, Any] = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task},
        ],
        "temperature": 0.2,
        "max_tokens": 2048,
    }
    if connector_spec.get("default_model"):
        payload["model"] = connector_spec["default_model"]
    return _dispatch_external(
        connector_spec.get("connector_id", "perplexity"),
        connector_spec.get("action", "chat_completions"),
        payload,
    )


def _handle_claude_desktop(*, entry: Dict[str, Any], task: str, connector_spec: Dict[str, Any]) -> str:
    payload: Dict[str, Any] = {
        "system": entry.get("system_prompt", ""),
        "messages": [{"role": "user", "content": task}],
    }
    if connector_spec.get("default_model"):
        payload["model"] = connector_spec["default_model"]
    return _dispatch_external(
        connector_spec.get("connector_id", "claude_desktop"),
        connector_spec.get("action", "messages"),
        payload,
    )


def _handle_copilot(*, entry: Dict[str, Any], task: str, connector_spec: Dict[str, Any]) -> str:
    return _dispatch_external(
        connector_spec.get("connector_id", "github_copilot"),
        connector_spec.get("action", "chat"),
        {"prompt": task, "system": entry.get("system_prompt", "")},
    )


def _handle_slack(*, entry: Dict[str, Any], task: str, connector_spec: Dict[str, Any]) -> str:
    channel = entry.get("slack_channel")
    if not channel:
        raise DAIRuntimeError(f"Sub-AI '{entry['name']}' has no slack_channel configured.")
    return _dispatch_external(
        connector_spec.get("connector_id", "slack_direct"),
        connector_spec.get("action", "post_message"),
        {"channel": channel, "text": task},
    )


def _handle_monday(*, entry: Dict[str, Any], task: str, connector_spec: Dict[str, Any]) -> str:
    board_id = entry.get("monday_board")
    if not board_id:
        raise DAIRuntimeError(f"Sub-AI '{entry['name']}' has no monday_board configured.")
    return _dispatch_external(
        connector_spec.get("connector_id", "monday"),
        connector_spec.get("action", "create_item"),
        {"board_id": board_id, "item_name": f"DAI: {task[:120]}", "task": task},
    )


def _handle_asana(*, entry: Dict[str, Any], task: str, connector_spec: Dict[str, Any]) -> str:
    project_id = entry.get("asana_project")
    if not project_id:
        raise DAIRuntimeError(f"Sub-AI '{entry['name']}' has no asana_project configured.")
    return _dispatch_external(
        connector_spec.get("connector_id", "asana_mcp_merge"),
        connector_spec.get("action", "create_task"),
        {"project": project_id, "name": f"DAI: {task[:120]}", "notes": task},
    )


_HANDLERS = {
    "perplexity": _handle_perplexity,
    "claude_desktop": _handle_claude_desktop,
    "copilot": _handle_copilot,
    "slack": _handle_slack,
    "monday": _handle_monday,
    "asana": _handle_asana,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> Any:
    if not path.exists():
        raise DAIRuntimeError(f"Required file missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DAIRuntimeError(f"Invalid JSON at {path}: {exc}") from exc


__all__ = ["route_task", "set_external_connector_dispatcher"]
