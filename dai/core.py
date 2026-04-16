"""
DAI.Core — core types, registry, Director interface.

This module defines the shared contracts every DAI agent speaks. Keep this
file small, dependency-free, and stable: changes here ripple across every
architect agent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

# ---------------------------------------------------------------------------
# Universal design unit
# ---------------------------------------------------------------------------

DESIGN_CATEGORIES = {
    "PA_Mode", "Subsystem", "Tool", "UI", "Backend", "Agent", "DAI_Module",
    "Test", "Doc",
}


@dataclass
class DesignSpec:
    """Universal design unit emitted by any architect agent."""
    name: str
    category: str                       # one of DESIGN_CATEGORIES
    description: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    test_plan: List[str] = field(default_factory=list)
    version: str = "0.1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.category not in DESIGN_CATEGORIES:
            raise ValueError(f"Unknown category: {self.category}")
        if not self.name:
            raise ValueError("DesignSpec.name is required")


@dataclass
class PAModeSpec:
    """Spec for a single PA.MasterFlow Mode."""
    name: str                           # e.g. "CheckDisk"
    description: str
    required_params: List[str] = field(default_factory=list)   # ⊆ {Param1..3}
    powerfx_validation: str = ""        # Power Fx boolean expression
    powerfx_routing_entry: str = ""     # e.g. '"CheckDisk", "Branch_CheckDisk",'
    branch_name: str = ""               # e.g. "Branch_CheckDisk"
    steps: List[str] = field(default_factory=list)
    helper_scripts: List[str] = field(default_factory=list)
    test_ideas: List[str] = field(default_factory=list)
    version: str = "0.1.0"

    def validate(self) -> None:
        allowed = {"Param1", "Param2", "Param3"}
        bad = set(self.required_params) - allowed
        if bad:
            raise ValueError(f"Invalid required_params: {bad}")
        if not self.branch_name:
            raise ValueError("PAModeSpec.branch_name is required")


# ---------------------------------------------------------------------------
# Agent protocol
# ---------------------------------------------------------------------------

class Agent(Protocol):
    """Every DAI architect implements this minimal interface."""
    name: str

    def design(self, target: str, **ctx: Any) -> DesignSpec: ...


# ---------------------------------------------------------------------------
# Registry — thin wrapper over system_map.yaml
# ---------------------------------------------------------------------------

class Registry:
    """Load, inspect, and update system_map.yaml."""

    def __init__(self, path: Path | str = "dai/system_map.yaml") -> None:
        self.path = Path(path)
        self._data: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]: ...
    def save(self) -> None: ...

    def get_module(self, name: str) -> Dict[str, Any]: ...
    def list_modes(self) -> List[str]: ...
    def register_mode(self, spec: PAModeSpec) -> None: ...
    def register_module(self, name: str, entry: Dict[str, Any]) -> None: ...
    def append_evolution(self, change: str, author: str) -> None: ...


# ---------------------------------------------------------------------------
# Director — top-level orchestrator
# ---------------------------------------------------------------------------

class Director:
    """
    DAI.Ultra entry point. Routes design requests to the right architect and
    keeps system_map.yaml consistent with emitted specs.
    """

    def __init__(self, registry: Optional[Registry] = None) -> None:
        self.registry = registry or Registry()
        self._agents: Dict[str, Agent] = {}

    # --- agent management -------------------------------------------------
    def register_agent(self, agent: Agent) -> None: ...
    def get_agent(self, name: str) -> Agent: ...

    # --- design dispatch --------------------------------------------------
    def design(self, category: str, target: str, **ctx: Any) -> DesignSpec: ...
    def design_pa_mode(self, name: str, **ctx: Any) -> PAModeSpec: ...

    # --- self-evolution ---------------------------------------------------
    def evolve(self, proposal: DesignSpec) -> None:
        """Apply a DAI.SelfArchitect proposal to system_map.yaml."""
        ...
