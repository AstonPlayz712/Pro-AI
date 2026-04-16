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


# ---------------------------------------------------------------------------
# Verification CLI — `python dai/core.py --verify`
# ---------------------------------------------------------------------------

_AGENT_IMPORTS = [
    ("dai.agents.subsystem_architect", "SubsystemArchitect"),
    ("dai.agents.pa_architect",        "PAArchitect"),
    ("dai.agents.code_architect",      "CodeArchitect"),
    ("dai.agents.ux_architect",        "UXArchitect"),
    ("dai.agents.backend_architect",   "BackendArchitect"),
    ("dai.agents.test_architect",      "TestArchitect"),
    ("dai.agents.doc_architect",       "DocArchitect"),
    ("dai.agents.self_architect",      "SelfArchitect"),
]


def _load_system_map(path: Path):
    """Best-effort load of system_map.yaml. Returns (data_or_none, error_or_none)."""
    if not path.exists():
        return None, f"not found: {path}"
    try:
        import yaml  # type: ignore
    except ImportError:
        return None, "PyYAML not installed (falling back to text checks)"
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f), None
    except Exception as e:  # pragma: no cover
        return None, f"parse error: {e}"


def verify_agents(director: "Director"):
    """Import and register every architect agent with the given Director.

    Returns (registered_names, errors).
    """
    import importlib

    registered: List[str] = []
    errors: List[str] = []
    for module_path, class_name in _AGENT_IMPORTS:
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            instance = cls()
            # Director.register_agent is currently a stub; populate directly
            # so verify output reflects actual registration state.
            director._agents[instance.name] = instance
            registered.append(instance.name)
        except Exception as e:
            errors.append(f"{module_path}.{class_name}: {e}")
    return registered, errors


def verify_modes(modes_dir: Path):
    """Scan pa_modes/*.yaml for registered PA modes. Returns (names, errors)."""
    errors: List[str] = []
    if not modes_dir.exists():
        errors.append(f"modes dir not found: {modes_dir}")
        return [], errors
    if not modes_dir.is_dir():
        errors.append(f"modes path is not a directory: {modes_dir}")
        return [], errors
    names = sorted(p.stem for p in modes_dir.glob("*.yaml"))
    return names, errors


def verify_masterflow(system_map, map_path: Path):
    """Confirm PA.MasterFlow shell is loadable. Returns (ok, message)."""
    if isinstance(system_map, dict):
        pm = system_map.get("pa_masterflow")
        if isinstance(pm, dict):
            name = pm.get("name", "PA.MasterFlow")
            kind = pm.get("kind", "?")
            return True, f"{name} shell loaded (kind={kind})"
        return False, "pa_masterflow section missing or malformed"
    # YAML unavailable — text fallback so the check is still meaningful.
    if not map_path.exists():
        return False, f"{map_path} not found"
    try:
        text = map_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"could not read {map_path}: {e}"
    if "pa_masterflow:" in text:
        return True, "pa_masterflow key present (text-mode check)"
    return False, "pa_masterflow key not found in system_map.yaml"


def verify_registry(registry: "Registry"):
    """Confirm the registry file is reachable. Returns (ok, message)."""
    path = Path(registry.path)
    if not path.exists():
        return False, f"registry file missing: {path}"
    if not path.is_file():
        return False, f"registry path not a file: {path}"
    return True, f"registry reachable at {path}"


def run_verify() -> int:
    """Full DAI.Ultra verification. Returns 0 on success, non-zero on failure."""
    try:
        from dai import __version__ as dai_version
    except Exception:
        dai_version = "unknown"

    print("=" * 72)
    print(" DAI.Ultra — System Verification")
    print("=" * 72)
    print(f" Version : {dai_version}")
    print()

    failures: List[str] = []

    # 1. Instantiate the Director
    try:
        director = Director()
        print("[ OK ] Director instantiated")
    except Exception as e:
        print(f"[FAIL] Director could not be instantiated: {e}")
        return 1

    # 2. Mode registry reachable
    ok, msg = verify_registry(director.registry)
    print(f"{'[ OK ]' if ok else '[FAIL]'} Registry: {msg}")
    if not ok:
        failures.append(f"registry: {msg}")

    # Parse system_map once for downstream checks.
    system_map, map_err = _load_system_map(Path(director.registry.path))
    if map_err:
        print(f"[WARN] system_map parse: {map_err}")

    # 3. PA.MasterFlow shell loadable
    ok, msg = verify_masterflow(system_map, Path(director.registry.path))
    print(f"{'[ OK ]' if ok else '[FAIL]'} PA.MasterFlow: {msg}")
    if not ok:
        failures.append(f"pa_masterflow: {msg}")

    # 4. Registered agents
    print()
    print("-- Registered Agents --------------------------------------------------")
    registered, agent_errors = verify_agents(director)
    if registered:
        for name in registered:
            print(f"  - {name}")
    else:
        print("  (none)")
    for err in agent_errors:
        print(f"  [FAIL] {err}")
        failures.append(f"agent: {err}")
    print(f"  total: {len(registered)} registered, {len(agent_errors)} errors")

    # 5. Registered PA modes
    print()
    print("-- PA.MasterFlow Modes ------------------------------------------------")
    modes_dir = Path("dai/pa_modes")
    modes, mode_errors = verify_modes(modes_dir)
    if modes:
        for name in modes:
            print(f"  - {name}")
    else:
        print("  (none)")
    for err in mode_errors:
        print(f"  [FAIL] {err}")
        failures.append(f"mode: {err}")
    print(f"  total: {len(modes)} modes discovered in {modes_dir}")

    # Summary
    print()
    print("=" * 72)
    if failures:
        print(f" RESULT: FAILED — {len(failures)} issue(s)")
        for f in failures:
            print(f"   - {f}")
        print("=" * 72)
        return 1
    print(" RESULT: PASSED")
    print("=" * 72)
    return 0


def _cli() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="dai.core",
        description="DAI.Ultra core — Director, shared types, verification CLI.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run full DAI.Ultra system verification and exit.",
    )
    args = parser.parse_args()

    if args.verify:
        return run_verify()

    parser.print_help()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_cli())
