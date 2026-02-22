"""Compatibility wrapper for shared debug logging.

The project-wide `debug_log` implementation lives at the repo root in debug_log.py.
This module remains to keep existing imports stable: `from core.debug_log import debug_log`.
"""

from __future__ import annotations

from debug_log import debug_log
