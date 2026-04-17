"""AutoLM — memory layer for AutoLink.

Simple in-memory store keyed by user_id. Stubs are intentionally minimal so
they can be replaced by a vector store / persistent backend later.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class AutoLM:
    """In-memory key/value store of recent task interactions per user."""

    def __init__(self) -> None:
        self._store: Dict[str, List[Dict[str, Any]]] = {}

    def load_memory(self, user_id: Optional[str]) -> List[Dict[str, Any]]:
        """Return recent memory entries for a user."""
        if user_id is None:
            return []
        return list(self._store.get(user_id, []))

    def save_memory(self, user_id: Optional[str], entry: Dict[str, Any]) -> None:
        """Append a memory entry for a user."""
        if user_id is None:
            return
        self._store.setdefault(user_id, []).append(entry)

    def search_memory(
        self, user_id: Optional[str], query: str
    ) -> List[Dict[str, Any]]:
        """Naive substring search over stored entries.

        TODO: replace with semantic search backed by a vector store.
        """
        if user_id is None or not query:
            return []
        needle = query.lower()
        return [
            entry
            for entry in self._store.get(user_id, [])
            if needle in str(entry).lower()
        ]
