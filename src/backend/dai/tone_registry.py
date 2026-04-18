"""
DAI tone registry.

Defines the built-in communication tones and a dataclass template for
user-defined tones.  The registry is a plain dict so tones can be looked
up by name at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ToneDefinition:
    """
    Describes a single communication tone.

    All string attributes use a shared vocabulary of levels:
    very_low | low | medium | high | very_high | neutral | tight | loose
    """

    verbosity: str
    warmth: str
    directness: str
    structure: str
    technicality: str
    formality: str
    name: str = ""

    def to_dict(self) -> dict:
        """Return a plain dict representation."""
        return {
            "name": self.name,
            "verbosity": self.verbosity,
            "warmth": self.warmth,
            "directness": self.directness,
            "structure": self.structure,
            "technicality": self.technicality,
            "formality": self.formality,
        }


# Built-in tones
ToneRegistry: Dict[str, ToneDefinition] = {
    "precise": ToneDefinition(
        name="precise",
        verbosity="low",
        warmth="neutral",
        directness="high",
        structure="tight",
        technicality="high",
        formality="medium",
    ),
    "conversational": ToneDefinition(
        name="conversational",
        verbosity="medium",
        warmth="high",
        directness="medium",
        structure="loose",
        technicality="low",
        formality="low",
    ),
    "minimalist": ToneDefinition(
        name="minimalist",
        verbosity="very_low",
        warmth="low",
        directness="very_high",
        structure="tight",
        technicality="medium",
        formality="medium",
    ),
    "technical": ToneDefinition(
        name="technical",
        verbosity="medium",
        warmth="low",
        directness="high",
        structure="tight",
        technicality="very_high",
        formality="high",
    ),
}


@dataclass
class NewTone:
    """
    Template for a user-defined tone.

    Users may supply any combination of the six tone attributes.
    Attributes default to "medium" / "neutral" when not specified so a
    partial definition is always valid.
    """

    name: str
    verbosity: str = "medium"
    warmth: str = "neutral"
    directness: str = "medium"
    structure: str = "medium"
    technicality: str = "medium"
    formality: str = "medium"

    def to_definition(self) -> ToneDefinition:
        """Convert to a ToneDefinition for registration."""
        return ToneDefinition(
            name=self.name,
            verbosity=self.verbosity,
            warmth=self.warmth,
            directness=self.directness,
            structure=self.structure,
            technicality=self.technicality,
            formality=self.formality,
        )


def register_tone(tone: NewTone) -> None:
    """Add a user-defined tone to the global ToneRegistry."""
    ToneRegistry[tone.name] = tone.to_definition()


__all__ = [
    "ToneDefinition",
    "ToneRegistry",
    "NewTone",
    "register_tone",
]
