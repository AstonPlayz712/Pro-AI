"""
DAI-Runtime · core.py
=====================

Cloud orchestrator core for DAI (Director AI).

Doctrine
--------
- DAI orchestrates; it does not execute. This module is the L0 runtime shell
  that lets the strategic mind reach external surfaces.
- All reasoning and generation calls go through Perplexity via
  ``perplexity_query()``.
- No local inference. No LM Studio. No GPU usage.
- Every Sub-AI invocation is funnelled through this module so the runtime
  remains the single chokepoint for credentials, logging, and policy.

Public surface
--------------
- ``perplexity_query(prompt, *, system=None, model=None, temperature=0.2,
  max_tokens=2048, timeout=60)`` — single canonical Perplexity call.
- ``run_subai(subai_name, task, *, registry_path=None, extra_context=None)``
  — load a Sub-AI's signature from the registry and dispatch the task.
- ``DAIRuntimeError`` — raised on configuration or transport failure.

Environment
-----------
- ``PERPLEXITY_API_KEY``         — required
- ``PERPLEXITY_API_BASE``        — optional, default ``https://api.perplexity.ai``
- ``PERPLEXITY_DEFAULT_MODEL``   — optional, default ``sonar-pro``

This module is intentionally dependency-light: only ``requests`` and
``python-dotenv`` are required at runtime.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests  # type: ignore
except ImportError as exc:  # pragma: no cover - hard dependency
    raise ImportError(
        "DAI-Runtime requires the 'requests' package. Install with "
        "`pip install requests`."
    ) from exc

try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover - graceful fallback
    def load_dotenv(*_args: Any, **_kwargs: Any) -> bool:
        return False


logger = logging.getLogger("dai_runtime")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _REPO_ROOT / ".env"
_REGISTRY_PATH_DEFAULT = Path(__file__).resolve().parent / "subai_registry.json"
_CONNECTORS_PATH_DEFAULT = Path(__file__).resolve().parent / "connectors.json"
_SYSTEM_PROMPT_PATH_DEFAULT = Path(__file__).resolve().parent / "system_prompt.txt"

DEFAULT_API_BASE = "https://api.perplexity.ai"
DEFAULT_MODEL = "sonar-pro"
CHAT_ENDPOINT = "/chat/completions"


class DAIRuntimeError(RuntimeError):
    """Raised when the runtime cannot satisfy a request."""


@dataclass(frozen=True)
class PerplexityConfig:
    api_key: str
    api_base: str = DEFAULT_API_BASE
    default_model: str = DEFAULT_MODEL


def _load_config() -> PerplexityConfig:
    """Read PERPLEXITY_API_KEY from .env (or environment) exactly once."""
    if _ENV_PATH.exists():
        load_dotenv(_ENV_PATH, override=False)

    api_key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
    if not api_key:
        raise DAIRuntimeError(
            "PERPLEXITY_API_KEY is not set. Add it to .env at the repo root "
            "or export it in the shell before invoking DAI-Runtime."
        )
    return PerplexityConfig(
        api_key=api_key,
        api_base=os.environ.get("PERPLEXITY_API_BASE", DEFAULT_API_BASE).rstrip("/"),
        default_model=os.environ.get("PERPLEXITY_DEFAULT_MODEL", DEFAULT_MODEL),
    )


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
    timeout: int = 60,
    extra_messages: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Send a chat completion to Perplexity and return the assistant text.

    Parameters
    ----------
    prompt : str
        The user message.
    system : str, optional
        System prompt. If omitted, the canonical DAI system prompt is loaded
        from ``system_prompt.txt``.
    model : str, optional
        Perplexity model id. Defaults to ``PERPLEXITY_DEFAULT_MODEL`` or
        ``sonar-pro``.
    temperature : float
        Sampling temperature.
    max_tokens : int
        Maximum tokens in the response.
    timeout : int
        HTTP timeout in seconds.
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
    config = _load_config()

    if system is None:
        system = _load_default_system_prompt()

    messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
    if extra_messages:
        messages.extend(extra_messages)
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model or config.default_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    url = f"{config.api_base}{CHAT_ENDPOINT}"

    logger.debug("perplexity_query → %s · model=%s", url, payload["model"])

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise DAIRuntimeError(f"Perplexity transport error: {exc}") from exc

    if response.status_code != 200:
        raise DAIRuntimeError(
            f"Perplexity returned {response.status_code}: {response.text[:500]}"
        )

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        raise DAIRuntimeError(
            f"Unexpected Perplexity response shape: {response.text[:500]}"
        ) from exc


def run_subai(
    subai_name: str,
    task: str,
    *,
    registry_path: Optional[Path] = None,
    extra_context: Optional[str] = None,
) -> str:
    """Look up a Sub-AI by name and dispatch its task.

    Sub-AIs whose connector is ``perplexity`` are executed inline through
    ``perplexity_query``. Sub-AIs that target a different connector are
    delegated to ``router.route_task`` so this module stays the chokepoint
    only for reasoning, not for non-Perplexity I/O.
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

    # Non-Perplexity connectors are handled by the router. Imported lazily to
    # avoid a circular import at module load time.
    from .router import route_task  # type: ignore  # noqa: WPS433
    return route_task(subai_name, task, registry=registry)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_default_system_prompt() -> str:
    if _SYSTEM_PROMPT_PATH_DEFAULT.exists():
        return _SYSTEM_PROMPT_PATH_DEFAULT.read_text(encoding="utf-8").strip()
    return (
        "You are DAI — Director AI. Orchestrate, do not execute. "
        "Use Perplexity as your execution engine."
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


__all__ = [
    "DAIRuntimeError",
    "PerplexityConfig",
    "perplexity_query",
    "run_subai",
]
