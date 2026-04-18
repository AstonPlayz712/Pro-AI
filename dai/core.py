"""
DAI.Core — core types, registry, Director interface.

This module defines the shared contracts every DAI agent speaks. Keep this
file small, dependency-free, and stable: changes here ripple across every
architect agent.
"""
from __future__ import annotations

import datetime
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

    def load(self) -> Dict[str, Any]:
        import yaml  # type: ignore
        if self._data is not None:
            return self._data
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}
        else:
            self._data = {}
        return self._data

    def save(self) -> None:
        import yaml  # type: ignore
        if self._data is None:
            return
        with self.path.open("w", encoding="utf-8") as f:
            yaml.dump(self._data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def get_module(self, name: str) -> Dict[str, Any]:
        data = self.load()
        modules = data.get("dai_modules", {})
        if name in modules:
            return modules[name]
        raise KeyError(f"Module {name!r} not found in registry")

    def list_modes(self) -> List[str]:
        data = self.load()
        pm = data.get("pa_masterflow", {})
        return list(pm.get("modes", {}).keys())

    def register_mode(self, spec: PAModeSpec) -> None:
        data = self.load()
        pm = data.setdefault("pa_masterflow", {})
        modes = pm.setdefault("modes", {})
        modes[spec.name] = {
            "branch": spec.branch_name,
            "description": spec.description,
            "version": spec.version,
        }

    def register_module(self, name: str, entry: Dict[str, Any]) -> None:
        data = self.load()
        modules = data.setdefault("dai_modules", {})
        modules[name] = entry

    def register_department(self, name: str, manifest: Dict[str, Any]) -> None:
        data = self.load()
        depts = data.setdefault("departments", {})
        depts[name] = manifest

    def register_endpoint(self, dept: str, endpoint: Dict[str, Any]) -> None:
        data = self.load()
        endpoints = data.setdefault("endpoints", {})
        dept_endpoints = endpoints.setdefault(dept, [])
        dept_endpoints.append(endpoint)

    def register_ux_panel(self, dept: str, panel: Dict[str, Any]) -> None:
        data = self.load()
        panels = data.setdefault("ux_panels", {})
        dept_panels = panels.setdefault(dept, [])
        dept_panels.append(panel)

    def append_evolution(self, change: str, author: str) -> None:
        data = self.load()
        log = data.setdefault("evolution_log", [])
        current_version = data.get("version", "0.1.0")
        log.append({
            "version": current_version,
            "date": datetime.date.today().isoformat(),
            "author": author,
            "change": change,
        })


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
    def register_agent(self, agent: Agent) -> None:
        self._agents[agent.name] = agent

    def get_agent(self, name: str) -> Agent:
        if name not in self._agents:
            raise KeyError(f"Agent {name!r} not registered")
        return self._agents[name]

    # --- design dispatch --------------------------------------------------
    def design(self, category: str, target: str, **ctx: Any) -> DesignSpec:
        if category not in DESIGN_CATEGORIES:
            raise ValueError(f"Unknown category: {category}")
        for agent in self._agents.values():
            try:
                spec = agent.design(target, category=category, **ctx)
                if spec is not None:
                    return spec
            except NotImplementedError:
                continue
        raise RuntimeError(f"No agent could handle design({category!r}, {target!r})")

    def design_pa_mode(self, name: str, **ctx: Any) -> PAModeSpec:
        agent = self.get_agent("DAI.PAArchitect")
        spec = agent.design(name, **ctx)
        return PAModeSpec(
            name=spec.name,
            description=spec.description,
            branch_name=spec.metadata.get("branch_name", f"Branch_{name}"),
            version=spec.version,
        )

    # --- department generation --------------------------------------------
    def generate_department(self, name: str, **ctx: Any) -> Dict[str, Any]:
        from dai.generator import generate_department
        return generate_department(name, registry=self.registry, **ctx)

    # --- self-evolution ---------------------------------------------------
    def evolve(self, proposal: DesignSpec) -> None:
        """Apply a DAI.SelfArchitect proposal to system_map.yaml."""
        ...
