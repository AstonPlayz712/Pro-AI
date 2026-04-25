"""
DAI-Runtime · router.py
=======================

Routing engine for DAI Sub-AI calls.

Reads ``subai_registry.json`` and dispatches a task to the connector named
on the Sub-AI's record. Connectors are described in ``connectors.json`` —
the router treats that file as the source of truth for endpoint shape and
command format.

Supported connectors (per the WIP spec):

- ``perplexity``     — funnel through ``core.perplexity_query``
- ``claude_desktop`` — local-host Anthropic-compatible HTTP shim
- ``copilot``        — GitHub Copilot CLI / Chat shim
- ``slack``          — Slack Web API (chat.postMessage)
- ``monday``         — Monday.com GraphQL API
- ``asana``          — Asana REST API

Anything not Perplexity is treated as an L0 surface call. The router never
makes autonomy decisions — it forwards.
"""

from __future__ import annotations

import json
import logging
import shlex
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import requests  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "DAI-Runtime router requires 'requests'. Install with `pip install requests`."
    ) from exc

from .core import DAIRuntimeError, perplexity_query  # noqa: WPS300

logger = logging.getLogger("dai_runtime.router")

_RUNTIME_DIR = Path(__file__).resolve().parent
_REGISTRY_PATH = _RUNTIME_DIR / "subai_registry.json"
_CONNECTORS_PATH = _RUNTIME_DIR / "connectors.json"


# ---------------------------------------------------------------------------
# External connector dispatcher
# ---------------------------------------------------------------------------
#
# Slack, Monday, and Asana are reached through external connectors provided by
# the host runtime (e.g. Perplexity Connectors, an MCP gateway, or a similar
# brokered surface). DAI-Runtime never holds tokens for these systems.
#
# To wire a real dispatcher, call ``set_external_connector_dispatcher(fn)``
# from your application bootstrap. The dispatcher receives
# ``(connector_id, action, payload)`` and must return a string response.
# Until a dispatcher is registered, calls raise DAIRuntimeError so the lack
# of wiring is visible rather than silent.

ExternalDispatcher = Callable[[str, str, Dict[str, Any]], str]
_external_dispatcher: Optional[ExternalDispatcher] = None


def set_external_connector_dispatcher(dispatcher: ExternalDispatcher) -> None:
    """Register the host-supplied function that calls external connectors."""
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

    Returns the connector's textual response. Raises ``DAIRuntimeError`` on
    routing or transport failure.
    """
    registry = registry if registry is not None else _read_json(_REGISTRY_PATH)
    connectors = connectors if connectors is not None else _read_json(_CONNECTORS_PATH)

    entry = next((s for s in registry if s["name"] == subai_name), None)
    if entry is None:
        raise DAIRuntimeError(f"Sub-AI '{subai_name}' not in registry.")

    connector_id = entry.get("connector", "perplexity").lower()
    connector_spec = connectors.get(connector_id)
    if connector_spec is None:
        raise DAIRuntimeError(
            f"Connector '{connector_id}' for Sub-AI '{subai_name}' is not defined "
            f"in connectors.json."
        )

    handler = _HANDLERS.get(connector_id)
    if handler is None:
        raise DAIRuntimeError(f"No router handler for connector '{connector_id}'.")

    logger.info("route_task → %s via %s", subai_name, connector_id)
    return handler(entry=entry, task=task, connector_spec=connector_spec)


# ---------------------------------------------------------------------------
# Connector handlers
# ---------------------------------------------------------------------------

def _handle_perplexity(*, entry: Dict[str, Any], task: str, connector_spec: Dict[str, Any]) -> str:
    system_prompt = entry.get("system_prompt") or ""
    model = connector_spec.get("default_model")
    return perplexity_query(prompt=task, system=system_prompt or None, model=model)


def _handle_claude_desktop(*, entry: Dict[str, Any], task: str, connector_spec: Dict[str, Any]) -> str:
    """Minimal HTTP shim. Assumes a local proxy that accepts a Claude-style payload."""
    endpoint = connector_spec.get("endpoint")
    if not endpoint:
        raise DAIRuntimeError("claude_desktop connector requires an 'endpoint' in connectors.json.")
    payload = {
        "system": entry.get("system_prompt", ""),
        "messages": [{"role": "user", "content": task}],
        "model": connector_spec.get("default_model", "claude-sonnet-4-6"),
    }
    return _post_json(endpoint, payload, timeout=connector_spec.get("timeout", 60))


def _handle_copilot(*, entry: Dict[str, Any], task: str, connector_spec: Dict[str, Any]) -> str:
    """Run via GitHub Copilot CLI when available; otherwise raise."""
    command_template = connector_spec.get("command")
    if not command_template:
        raise DAIRuntimeError("copilot connector requires a 'command' template in connectors.json.")
    cmd = command_template.replace("{task}", shlex.quote(task))
    try:
        completed = subprocess.run(
            cmd, shell=True, check=False, capture_output=True, text=True,
            timeout=connector_spec.get("timeout", 120),
        )
    except subprocess.TimeoutExpired as exc:
        raise DAIRuntimeError(f"Copilot CLI timed out: {exc}") from exc
    if completed.returncode != 0:
        raise DAIRuntimeError(
            f"Copilot CLI exit {completed.returncode}: {completed.stderr.strip()[:500]}"
        )
    return completed.stdout.strip()


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


def _post_json(
    url: str,
    payload: Dict[str, Any],
    *,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
) -> str:
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise DAIRuntimeError(f"HTTP transport error to {url}: {exc}") from exc
    if response.status_code >= 400:
        raise DAIRuntimeError(
            f"{url} returned {response.status_code}: {response.text[:500]}"
        )
    return response.text


__all__ = ["route_task", "set_external_connector_dispatcher"]
