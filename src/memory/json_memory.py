"""JSON-based memory storage for conversations"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ConversationEntry:
    """Represents a single conversation entry"""

    timestamp: str
    role: str  # "user" or "assistant"
    content: str
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class JSONMemory:
    """JSON-based memory management for conversation history"""

    def __init__(self, memory_file: str = "data/memory.json", max_entries: int = 1000):
        """
        Initialize JSON memory storage.

        Args:
            memory_file: Path to the JSON memory file
            max_entries: Maximum number of entries to keep
        """
        self.memory_file = memory_file
        self.max_entries = max_entries
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create memory file and directory if they don't exist"""
        directory = os.path.dirname(self.memory_file)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        if not os.path.exists(self.memory_file):
            with open(self.memory_file, "w") as f:
                json.dump({"conversations": []}, f, indent=2)

    def add_entry(self, role: str, content: str, model: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Add a new entry to memory.

        Args:
            role: "user" or "assistant"
            content: The message content
            model: The model used (if assistant)
            metadata: Additional metadata
        """
        entry = ConversationEntry(
            timestamp=datetime.now().isoformat(),
            role=role,
            content=content,
            model=model,
            metadata=metadata or {},
        )

        with open(self.memory_file, "r") as f:
            data = json.load(f)

        data["conversations"].append(asdict(entry))

        # Keep only recent entries
        if len(data["conversations"]) > self.max_entries:
            data["conversations"] = data["conversations"][-self.max_entries :]

        with open(self.memory_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_recent(self, limit: int = 10) -> List[ConversationEntry]:
        """
        Get recent conversation entries.

        Args:
            limit: Number of recent entries to retrieve

        Returns:
            List of recent ConversationEntry objects
        """
        with open(self.memory_file, "r") as f:
            data = json.load(f)

        entries = data.get("conversations", [])
        entries = entries[-limit:] if limit else entries

        return [
            ConversationEntry(
                timestamp=e["timestamp"],
                role=e["role"],
                content=e["content"],
                model=e.get("model"),
                metadata=e.get("metadata"),
            )
            for e in entries
        ]

    def get_all(self) -> List[ConversationEntry]:
        """Get all conversation entries"""
        return self.get_recent(limit=None)

    def clear(self):
        """Clear all conversation history"""
        with open(self.memory_file, "w") as f:
            json.dump({"conversations": []}, f, indent=2)

    def get_context(self, limit: int = 5) -> str:
        """
        Get conversation context as a formatted string.

        Args:
            limit: Number of recent entries to include

        Returns:
            Formatted conversation history
        """
        entries = self.get_recent(limit)
        context = []

        for entry in entries:
            role = entry.role.capitalize()
            context.append(f"{role}: {entry.content}")

        return "\n".join(context)
