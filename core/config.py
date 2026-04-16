"""
config.py — Central configuration loader for the Pro-AI / Director-AI stack.

Loads API keys from environment (and optional .env file via python-dotenv)
and exposes helper factories that build the correct vision and web tools
based on which credentials are available.

Lookup priority
---------------
Vision (create_vision_tool):
  1. ANTHROPIC_API_KEY  → ClaudeVisionTool    (claude-sonnet-4-6)
  2. OPENAI_API_KEY     → OpenAIVisionTool    (gpt-4o)
  3. GOOGLE_API_KEY     → GeminiVisionTool    (gemini-1.5-pro)
  4. (none)             → NullVisionInterface

Web (create_web_tool):
  1. GOOGLE_API_KEY (+ GOOGLE_CSE_ID) → GoogleSearchTool
  2. BRAVE_API_KEY                    → BraveSearchTool
  3. (none)                           → DuckDuckGoWebInterface
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from director.tools.vision.interface import VisionInterface
    from director.tools.web.interface import WebInterface

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# .env loading (best-effort — dotenv is optional)
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    """Load environment variables from a .env file at the repo root if present."""
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        logger.debug("python-dotenv not installed; skipping .env auto-load.")
        return

    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / ".env"
        if candidate.exists():
            load_dotenv(candidate, override=False)
            logger.info("Loaded environment from %s", candidate)
            return


_load_dotenv()


# ---------------------------------------------------------------------------
# Config dataclass
# ---------------------------------------------------------------------------

@dataclass
class AppConfig:
    anthropic_api_key: str | None = None
    openai_api_key:    str | None = None
    google_api_key:    str | None = None
    google_cse_id:     str | None = None
    brave_api_key:     str | None = None

    # Model overrides (optional)
    anthropic_model: str = "claude-sonnet-4-6"
    openai_model:    str = "gpt-4o"
    gemini_model:    str = "gemini-1.5-pro"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Uploads
    upload_dir: str = "uploads"
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            google_cse_id=os.getenv("GOOGLE_CSE_ID"),
            brave_api_key=os.getenv("BRAVE_API_KEY"),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
            host=os.getenv("DAI_HOST", "0.0.0.0"),
            port=int(os.getenv("DAI_PORT", "8000")),
            upload_dir=os.getenv("DAI_UPLOAD_DIR", "uploads"),
            max_upload_bytes=int(os.getenv("DAI_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024))),
        )

    # ------------------------------------------------------------------
    # Tool factories (instance methods)
    # ------------------------------------------------------------------

    def build_vision_tool(self) -> "VisionInterface":
        return create_vision_tool(self)

    def build_web_tool(self) -> "WebInterface":
        return create_web_tool(self)


# ---------------------------------------------------------------------------
# Module-level tool factories
# ---------------------------------------------------------------------------

def create_vision_tool(cfg: "AppConfig | None" = None) -> "VisionInterface":
    """
    Build a VisionInterface based on available API keys.

    Priority: Anthropic → OpenAI → Google (Gemini) → Null.
    """
    cfg = cfg or get_config()
    from director.tools.vision.interface import NullVisionInterface

    if cfg.anthropic_api_key:
        try:
            from director.tools.vision.interface import ClaudeVisionInterface
            os.environ.setdefault("ANTHROPIC_API_KEY", cfg.anthropic_api_key)
            logger.info("Vision backend: ClaudeVisionTool (%s)", cfg.anthropic_model)
            return ClaudeVisionInterface(model=cfg.anthropic_model)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("ClaudeVisionTool init failed: %s", exc)

    if cfg.openai_api_key:
        try:
            from director.tools.vision.openai_vision import OpenAIVisionInterface
            os.environ.setdefault("OPENAI_API_KEY", cfg.openai_api_key)
            logger.info("Vision backend: OpenAIVisionTool (%s)", cfg.openai_model)
            return OpenAIVisionInterface(model=cfg.openai_model)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("OpenAIVisionTool init failed: %s", exc)

    if cfg.google_api_key:
        try:
            from director.tools.vision.gemini_vision import GeminiVisionInterface
            os.environ.setdefault("GOOGLE_API_KEY", cfg.google_api_key)
            logger.info("Vision backend: GeminiVisionTool (%s)", cfg.gemini_model)
            return GeminiVisionInterface(
                api_key=cfg.google_api_key,
                model=cfg.gemini_model,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("GeminiVisionTool init failed: %s", exc)

    logger.info("Vision backend: NullVisionInterface (no API keys present)")
    return NullVisionInterface()


def create_web_tool(cfg: "AppConfig | None" = None) -> "WebInterface":
    """
    Build a WebInterface based on available API keys.

    Priority: Google CSE → Brave Search → DuckDuckGo.
    """
    cfg = cfg or get_config()
    from director.tools.web.interface import DuckDuckGoWebInterface

    if cfg.google_api_key and cfg.google_cse_id:
        try:
            from director.tools.web.google_web import GoogleWebInterface
            logger.info("Web backend: GoogleSearchTool")
            return GoogleWebInterface(
                api_key=cfg.google_api_key,
                cse_id=cfg.google_cse_id,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("GoogleSearchTool init failed: %s", exc)

    if cfg.brave_api_key:
        try:
            from director.tools.web.brave_web import BraveWebInterface
            logger.info("Web backend: BraveSearchTool")
            return BraveWebInterface(api_key=cfg.brave_api_key)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("BraveSearchTool init failed: %s", exc)

    logger.info("Web backend: DuckDuckGoWebInterface")
    return DuckDuckGoWebInterface()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Return the process-wide AppConfig singleton."""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config


def reload_config() -> AppConfig:
    """Force reload the config (used for tests)."""
    global _config
    _config = AppConfig.from_env()
    return _config
