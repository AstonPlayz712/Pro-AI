"""
DAI-Runtime · core.py
=====================

Cloud orchestrator core for DAI (Director AI).

Doctrine
--------
- DAI orchestrates; it does not execute. This module is the L0 runtime shell
  that lets the strategic mind reach external surfaces.
- **Connector-first architecture.** Every outbound call — including
  Perplexity — leaves through the host's external-connector dispatcher.
  DAI-Runtime never holds API keys, bearer tokens, or raw HTTP credentials.
- No local inference. No LM Studio. No GPU usage.
- Every Sub-AI invocation is funnelled through this module so the runtime
  remains the single chokepoint for routing, logging, and policy.

Public surface
--------------
- ``perplexity_query(prompt, *, system=None, model=None, temperature=0.2,
  max_tokens=2048)`` — single canonical Perplexity call routed via the
  Perplexity Connector.
- ``run_subai(subai_name, task, *, registry_path=None, extra_context=None)``
  — load a Sub-AI's signature from the registry and dispatch the task.
- ``DAIRuntimeError`` — raised on configuration or transport failure.
- ``set_external_connector_dispatcher(fn)`` — re-exported from ``router``;
  the host registers its connector surface here.

Bootstrap
---------
The host application (VS Code extension, MCP gateway, Perplexity-Connector
client) MUST register a dispatcher at startup:

    from dai_runtime.core import set_external_connector_dispatcher

    def my_dispatcher(connector_id: str, action: str, payload: dict) -> str:
        ...

    set_external_connector_dispatcher(my_dispatcher)

Until a dispatcher is registered, every call raises ``DAIRuntimeError`` so
the missing wiring is visible rather than silent.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("dai_runtime")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_RUNTIME_DIR = Path(__file__).resolve().parent
_REGISTRY_PATH_DEFAULT = _RUNTIME_DIR / "subai_registry.json"
_CONNECTORS_PATH_DEFAULT = _RUNTIME_DIR / "connectors.json"
_SYSTEM_PROMPT_PATH_DEFAULT = _RUNTIME_DIR / "system_prompt.txt"


class DAIRuntimeError(RuntimeError):
    """Raised when the runtime cannot satisfy a request."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def perplexity_query(
    prompt: str,
    *,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    extra_messages: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Run a reasoning call through the Perplexity Connector.

    All parameters are passed as a payload to the dispatcher; the host
    connector is responsible for authentication, model selection, and
    transport. The runtime never opens an HTTP socket of its own.

    Parameters
    ----------
    prompt : str
        The user message.
    system : str, optional
        System prompt. Defaults to the canonical DAI system prompt loaded
        from ``system_prompt.txt``.
    model : str, optional
        Perplexity model id. ``None`` means "let the connector choose".
    temperature : float
        Sampling temperature.
    max_tokens : int
        Maximum tokens in the response.
    extra_messages : list, optional
        Additional message dicts inserted between system and user prompts
        (e.g. prior turns for an autonomy loop).

    Returns
    -------
    str
        The assistant message content.

    Raises
    ------
    DAIRuntimeError
        On configuration or transport failure.
    """
    if system is None:
        system = _load_default_system_prompt()

    messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
    if extra_messages:
        messages.extend(extra_messages)
    messages.append({"role": "user", "content": prompt})

    connector_spec = _load_connector_spec("perplexity")
    payload: Dict[str, Any] = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if model is not None:
        payload["model"] = model
    elif connector_spec.get("default_model"):
        payload["model"] = connector_spec["default_model"]

    # Lazy import to avoid a circular dependency at module load time.
    from .router import _dispatch_external  # type: ignore  # noqa: WPS433

    logger.debug(
        "perplexity_query → connector=%s action=%s model=%s",
        connector_spec.get("connector_id", "perplexity"),
        connector_spec.get("action", "chat_completions"),
        payload.get("model"),
    )

    return _dispatch_external(
        connector_spec.get("connector_id", "perplexity"),
        connector_spec.get("action", "chat_completions"),
        payload,
    )


def run_subai(
    subai_name: str,
    task: str,
    *,
    registry_path: Optional[Path] = None,
    extra_context: Optional[str] = None,
) -> str:
    """Look up a Sub-AI by name and dispatch its task.

    Sub-AIs whose connector is ``perplexity`` are executed through
    ``perplexity_query`` (which itself delegates to the Perplexity
    Connector). Sub-AIs targeting any other connector are dispatched via
    ``router.route_task``. Either way, every outbound call leaves through
    the host's connector dispatcher.
    """
    registry = _load_registry(registry_path or _REGISTRY_PATH_DEFAULT)
    entry = next((s for s in registry if s["name"] == subai_name), None)
    if entry is None:
        raise DAIRuntimeError(f"Sub-AI '{subai_name}' not found in registry.")

    connector = entry.get("connector", "perplexity").lower()
    sub_system_prompt = entry.get("system_prompt") or _load_default_system_prompt()

    if extra_context:
        sub_system_prompt = f"{sub_system_prompt}\n\n# Additional context\n{extra_context}"

    if connector == "perplexity":
        return perplexity_query(prompt=task, system=sub_system_prompt)

    from .router import route_task  # type: ignore  # noqa: WPS433
    return route_task(subai_name, task, registry=registry)


# Re-export so callers can bootstrap from a single module.
def set_external_connector_dispatcher(dispatcher: Any) -> None:
    """Register the host-supplied connector dispatcher (re-export of router)."""
    from .router import set_external_connector_dispatcher as _set  # noqa: WPS433
    _set(dispatcher)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_default_system_prompt() -> str:
    if _SYSTEM_PROMPT_PATH_DEFAULT.exists():
        return _SYSTEM_PROMPT_PATH_DEFAULT.read_text(encoding="utf-8").strip()
    return (
        "You are DAI — Director AI. Orchestrate, do not execute. "
        "Use the Perplexity Connector as your execution engine."
    )


def _load_registry(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise DAIRuntimeError(f"Sub-AI registry not found at {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DAIRuntimeError(f"Sub-AI registry is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise DAIRuntimeError("Sub-AI registry must be a JSON list.")
    return data


def _load_connector_spec(connector_id: str) -> Dict[str, Any]:
    if not _CONNECTORS_PATH_DEFAULT.exists():
        raise DAIRuntimeError(f"connectors.json missing at {_CONNECTORS_PATH_DEFAULT}")
    try:
        data = json.loads(_CONNECTORS_PATH_DEFAULT.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DAIRuntimeError(f"connectors.json is not valid JSON: {exc}") from exc
    spec = data.get(connector_id)
    if not isinstance(spec, dict):
        raise DAIRuntimeError(f"Connector '{connector_id}' not defined in connectors.json")
    return spec


__all__ = [
    "DAIRuntimeError",
    "perplexity_query",
    "run_subai",
    "set_external_connector_dispatcher",
]
