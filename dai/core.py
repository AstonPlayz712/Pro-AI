"""
DAI.Core — core types, registry, Director interface.

This module defines the shared contracts every DAI agent speaks. Keep this
file small, dependency-free, and stable: changes here ripple across every
architect agent.

CLI
---
    python dai/core.py --verify                     # validate repo integrity
    python dai/core.py --generate-department NAME   # scaffold a department
"""
from __future__ import annotations

import argparse
import datetime
import importlib
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

import yaml

logger = logging.getLogger(__name__)

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
        """Load system_map.yaml from disk (cached after first call)."""
        if self._data is None:
            with open(self.path, "r", encoding="utf-8") as fh:
                self._data = yaml.safe_load(fh) or {}
        return self._data

    def save(self) -> None:
        """Persist the in-memory map back to disk."""
        if self._data is None:
            return
        with open(self.path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(self._data, fh, default_flow_style=False, sort_keys=False)

    def get_module(self, name: str) -> Dict[str, Any]:
        """Return the dict entry for a DAI module by dotted name."""
        data = self.load()
        modules = data.get("dai_modules", {})
        if name not in modules:
            raise KeyError(f"Module {name!r} not found in system_map")
        return modules[name]

    def list_modes(self) -> List[str]:
        """Return the names of all registered PA.MasterFlow modes."""
        data = self.load()
        modes = data.get("pa_masterflow", {}).get("modes", {})
        return list(modes.keys())

    def register_mode(self, spec: PAModeSpec) -> None:
        """Insert / update a PA mode entry."""
        data = self.load()
        modes = data.setdefault("pa_masterflow", {}).setdefault("modes", {})
        modes[spec.name] = {
            "description": spec.description,
            "branch_name": spec.branch_name,
            "required_params": spec.required_params,
            "version": spec.version,
        }

    def register_module(self, name: str, entry: Dict[str, Any]) -> None:
        """Insert / update a DAI module entry."""
        data = self.load()
        data.setdefault("dai_modules", {})[name] = entry

    def append_evolution(self, change: str, author: str) -> None:
        """Append a record to the evolution log."""
        data = self.load()
        log = data.setdefault("evolution_log", [])
        log.append({
            "version": data.get("version", "0.1.0"),
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
        """Register an architect agent by its ``name`` attribute."""
        self._agents[agent.name] = agent

    def get_agent(self, name: str) -> Agent:
        """Look up a registered architect by name."""
        if name not in self._agents:
            raise KeyError(f"Agent {name!r} not registered")
        return self._agents[name]

    # --- design dispatch --------------------------------------------------
    def design(self, category: str, target: str, **ctx: Any) -> DesignSpec:
        """Route a design request to the first agent that handles *category*."""
        for agent in self._agents.values():
            try:
                spec = agent.design(target, category=category, **ctx)
                if spec is not None:
                    return spec
            except NotImplementedError:
                continue
        raise RuntimeError(
            f"No agent could handle category={category!r}, target={target!r}"
        )

    def design_pa_mode(self, name: str, **ctx: Any) -> PAModeSpec:
        """Convenience: ask the PAArchitect to design a PA mode."""
        pa = self.get_agent("DAI.PAArchitect")
        return pa.design_mode(name, **ctx)  # type: ignore[attr-defined]

    # --- self-evolution ---------------------------------------------------
    def evolve(self, proposal: DesignSpec) -> None:
        """Apply a DAI.SelfArchitect proposal to system_map.yaml."""
        proposal.validate()
        self.registry.register_module(proposal.name, {
            "category": proposal.category,
            "description": proposal.description,
            "version": proposal.version,
        })
        self.registry.append_evolution(
            change=f"Added {proposal.name} ({proposal.category})",
            author="DAI.SelfArchitect",
        )
        self.registry.save()


# ---------------------------------------------------------------------------
# Department generator
# ---------------------------------------------------------------------------

def generate_department(name: str) -> DesignSpec:
    """
    Scaffold a new department DesignSpec.

    A *department* is a top-level subsystem grouping (e.g. "BuilderOS")
    that bundles backend, UX, agent, and test components.
    """
    spec = DesignSpec(
        name=name,
        category="Subsystem",
        description=f"{name} department — auto-generated scaffold.",
        components=[
            f"{name}.Backend",
            f"{name}.UX",
            f"{name}.Agent",
            f"{name}.Tests",
            f"{name}.Docs",
        ],
        steps=[
            f"Create directory structure under departments/{name.lower()}/",
            "Implement backend service stubs",
            "Implement UX screen stubs",
            "Register department agent with Director",
            "Generate initial test harness",
            "Generate README and developer guide",
        ],
        test_plan=[
            f"Unit tests for {name}.Backend",
            f"Integration test for {name}.Agent registration",
            f"UX smoke test for {name}.UX",
        ],
    )
    spec.validate()
    return spec


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

_AGENT_MODULES = [
    "dai.agents.subsystem_architect",
    "dai.agents.pa_architect",
    "dai.agents.code_architect",
    "dai.agents.ux_architect",
    "dai.agents.backend_architect",
    "dai.agents.test_architect",
    "dai.agents.doc_architect",
    "dai.agents.self_architect",
]


def verify() -> bool:
    """Run post-rebase integrity checks. Returns True if everything passes."""
    ok = True

    # 1. Syntax of this file (already running, so implicitly OK)
    print("✓ dai/core.py syntax OK")

    # 2. Agent module imports
    for mod_name in _AGENT_MODULES:
        try:
            importlib.import_module(mod_name)
            print(f"✓ import {mod_name}")
        except Exception as exc:
            print(f"✗ import {mod_name}: {exc}")
            ok = False

    # 3. Registry can load system_map.yaml
    try:
        reg = Registry()
        data = reg.load()
        n_modules = len(data.get("dai_modules", {}))
        print(f"✓ Registry loaded system_map.yaml ({n_modules} modules)")
    except Exception as exc:
        print(f"✗ Registry load failed: {exc}")
        ok = False

    # 4. Director + Registry round-trip
    try:
        director = Director(registry=Registry())
        assert director.registry is not None
        assert isinstance(director._agents, dict)
        print("✓ Director instantiation OK")
    except Exception as exc:
        print(f"✗ Director instantiation: {exc}")
        ok = False

    # 5. DesignSpec / PAModeSpec validation
    try:
        ds = DesignSpec(name="test", category="Subsystem", description="t")
        ds.validate()
        print("✓ DesignSpec validation OK")
    except Exception as exc:
        print(f"✗ DesignSpec validation: {exc}")
        ok = False

    try:
        pm = PAModeSpec(name="t", description="t", branch_name="Branch_T")
        pm.validate()
        print("✓ PAModeSpec validation OK")
    except Exception as exc:
        print(f"✗ PAModeSpec validation: {exc}")
        ok = False

    return ok


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dai.core",
        description="DAI.Core — core types, registry, and Director CLI.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run post-rebase integrity checks.",
    )
    parser.add_argument(
        "--generate-department",
        metavar="NAME",
        help="Generate a department scaffold DesignSpec and print it as JSON.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verify:
        print("=" * 60)
        print("DAI.Core — post-rebase verification")
        print("=" * 60)
        ok = verify()
        print("=" * 60)
        if ok:
            print("ALL CHECKS PASSED ✓")
        else:
            print("SOME CHECKS FAILED ✗")
            sys.exit(1)
        return

    if args.generate_department:
        name = args.generate_department
        spec = generate_department(name)
        print(json.dumps(asdict(spec), indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    # Ensure the repo root is on sys.path so `dai.*` imports resolve.
    _repo_root = str(Path(__file__).resolve().parent.parent)
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)
    main()
