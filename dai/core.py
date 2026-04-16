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

import yaml

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
        if self._data is None:
            if self.path.exists():
                self._data = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
            else:
                self._data = {}
        return self._data

    def save(self) -> None:
        self.path.write_text(
            yaml.dump(self.load(), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def get_module(self, name: str) -> Dict[str, Any]:
        return self.load().get("dai_modules", {}).get(name, {})

    def list_modes(self) -> List[str]:
        data = self.load()
        # Modes registered in system_map.yaml under pa_masterflow.modes
        map_modes = list(data.get("pa_masterflow", {}).get("modes", {}).keys())
        # Also discover YAML specs in the sibling pa_modes/ directory
        pa_modes_dir = self.path.parent / "pa_modes"
        file_modes = [f.stem for f in sorted(pa_modes_dir.glob("*.yaml"))] if pa_modes_dir.exists() else []
        # Return a deduplicated, sorted union
        return sorted(set(map_modes) | set(file_modes))

    def register_mode(self, spec: PAModeSpec) -> None:
        data = self.load()
        data.setdefault("pa_masterflow", {}).setdefault("modes", {})[spec.name] = {
            "branch": spec.branch_name,
            "required_params": spec.required_params,
            "version": spec.version,
        }
        self.save()

    def register_module(self, name: str, entry: Dict[str, Any]) -> None:
        data = self.load()
        data.setdefault("dai_modules", {})[name] = entry
        self.save()

    def append_evolution(self, change: str, author: str) -> None:
        from datetime import date
        data = self.load()
        data.setdefault("evolution_log", []).append({
            "version": data.get("version", "0.1.0"),
            "date": date.today().isoformat(),
            "author": author,
            "change": change,
        })
        self.save()


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
            raise KeyError(f"No agent registered under name {name!r}")
        return self._agents[name]

    # --- design dispatch --------------------------------------------------
    def design(self, category: str, target: str, **ctx: Any) -> DesignSpec: ...
    def design_pa_mode(self, name: str, **ctx: Any) -> PAModeSpec: ...

    # --- self-evolution ---------------------------------------------------
    def evolve(self, proposal: DesignSpec) -> None:
        """Apply a DAI.SelfArchitect proposal to system_map.yaml."""
        ...


# ---------------------------------------------------------------------------
# Verification helpers
# ---------------------------------------------------------------------------

def verify_agents(registry_data: Dict[str, Any]) -> List[str]:
    """Return list of agent names declared in the system_map dai_modules section."""
    return list(registry_data.get("dai_modules", {}).keys())


def verify_modes(registry_data: Dict[str, Any], pa_modes_dir: Path) -> List[str]:
    """Return deduplicated list of PA mode names from the pa_modes/ directory
    and the pa_masterflow.modes table in system_map."""
    map_modes = list(registry_data.get("pa_masterflow", {}).get("modes", {}).keys())
    file_modes = (
        [f.stem for f in sorted(pa_modes_dir.glob("*.yaml"))]
        if pa_modes_dir.exists()
        else []
    )
    return sorted(set(map_modes) | set(file_modes))


def verify_pa_masterflow(registry_data: Dict[str, Any]) -> bool:
    """Return True when the PA.MasterFlow shell section is present and valid."""
    pa = registry_data.get("pa_masterflow", {})
    return bool(pa.get("name") == "PA.MasterFlow" and pa.get("kind"))


def run_verify(
    system_map_path: Optional[Path] = None,
    pa_modes_dir: Optional[Path] = None,
) -> int:
    """
    Run a full DAI.Ultra system verification and print a human-readable
    report.  Returns 0 on success, 1 on failure.
    """
    _here = Path(__file__).parent
    if system_map_path is None:
        system_map_path = _here / "system_map.yaml"
    if pa_modes_dir is None:
        pa_modes_dir = _here / "pa_modes"

    print("=" * 60)
    print("  DAI.Ultra — System Verification Report")
    print("=" * 60)

    failures: List[str] = []
    registry_data: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Step 1 — Mode registry (system_map.yaml)
    # ------------------------------------------------------------------
    print("\n[1] Mode registry (system_map.yaml)")
    try:
        registry_data = yaml.safe_load(
            system_map_path.read_text(encoding="utf-8")
        ) or {}
        print(f"    ✓  Loaded: {system_map_path}")
        print(f"    ✓  Schema version  : {registry_data.get('schema_version', 'n/a')}")
        print(f"    ✓  DAI.Ultra version: {registry_data.get('version', 'n/a')}")
    except Exception as exc:
        print(f"    ✗  Failed to load registry: {exc}")
        failures.append(f"registry: {exc}")

    # ------------------------------------------------------------------
    # Step 2 — Director instantiation
    # ------------------------------------------------------------------
    print("\n[2] Director instantiation")
    try:
        registry = Registry(path=system_map_path)
        director = Director(registry=registry)
        print("    ✓  Director instantiated successfully")
    except Exception as exc:
        print(f"    ✗  Director instantiation failed: {exc}")
        failures.append(f"director: {exc}")

    # ------------------------------------------------------------------
    # Step 3 — Registered agents
    # ------------------------------------------------------------------
    print("\n[3] Registered agents")
    agents = verify_agents(registry_data)
    if agents:
        for agent_name in agents:
            print(f"    •  {agent_name}")
        print(f"    ✓  {len(agents)} agent(s) found")
    else:
        print("    ✗  No agents found in registry")
        failures.append("agents: none registered in dai_modules")

    # ------------------------------------------------------------------
    # Step 4 — Registered PA modes
    # ------------------------------------------------------------------
    print("\n[4] Registered PA modes")
    modes = verify_modes(registry_data, pa_modes_dir)
    if modes:
        for mode_name in modes:
            print(f"    •  {mode_name}")
        print(f"    ✓  {len(modes)} mode(s) found")
    else:
        print("    ⚠  No PA modes found (pa_modes/ directory empty or missing)")

    # ------------------------------------------------------------------
    # Step 5 — PA.MasterFlow shell loadable
    # ------------------------------------------------------------------
    print("\n[5] PA.MasterFlow shell")
    if verify_pa_masterflow(registry_data):
        pa = registry_data.get("pa_masterflow", {})
        inputs = [i["name"] for i in pa.get("inputs", [])]
        print("    ✓  PA.MasterFlow shell is loadable")
        print(f"    ✓  Kind   : {pa.get('kind')}")
        print(f"    ✓  Inputs : {', '.join(inputs)}")
    else:
        print("    ✗  PA.MasterFlow shell section missing or invalid")
        failures.append("pa_masterflow: shell not loadable")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    if failures:
        print(f"  RESULT: FAILED  ({len(failures)} issue(s))")
        for item in failures:
            print(f"    ✗  {item}")
        print("=" * 60)
        return 1

    print("  RESULT: ALL CHECKS PASSED")
    print("=" * 60)
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="python dai/core.py",
        description="DAI.Ultra — Core CLI",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run full system verification and print a health report.",
    )
    args = parser.parse_args()

    if args.verify:
        sys.exit(run_verify())
    else:
        parser.print_help()
        sys.exit(0)
