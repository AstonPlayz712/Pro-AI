"""DAI.DepartmentGenerator — scaffold new departments with folder structure,
manifest, and registry entries."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from dai.core import Registry

# Default Sub-AIs every department gets
DEFAULT_SUBAIS = ["Planner", "Executor", "Monitor"]

# Default department purposes
DEPARTMENT_PURPOSES: Dict[str, str] = {
    "BuilderOS": "Operating-system-level build orchestration and device provisioning",
    "Auto": "Automation pipelines, CI/CD, and workflow execution",
    "ITS": "IT support, diagnostics, and remediation",
}


class DepartmentGenerator:
    """Creates the folder scaffold and initial files for a new department."""

    def __init__(self, *, registry: Registry, base_dir: Path) -> None:
        self.registry = registry
        self.base = base_dir

    def generate(self, name: str, **ctx: Any) -> Dict[str, Any]:
        dept_dir = self.base / "dai" / "departments" / name.lower()
        files_created: List[str] = []

        # Create directory tree
        for subdir in [
            dept_dir,
            dept_dir / "subais",
        ]:
            subdir.mkdir(parents=True, exist_ok=True)

        # __init__.py
        init_path = dept_dir / "__init__.py"
        purpose = ctx.get("purpose", DEPARTMENT_PURPOSES.get(name, f"{name} department"))
        init_path.write_text(
            f'"""DAI Department: {name} — {purpose}"""\n\n'
            f'DEPARTMENT_NAME = "{name}"\n'
            f'DEPARTMENT_PURPOSE = "{purpose}"\n',
            encoding="utf-8",
        )
        files_created.append(str(init_path))

        # manifest.yaml
        manifest_path = dept_dir / "manifest.yaml"
        subais = ctx.get("subais", [f"{name}.{s}" for s in DEFAULT_SUBAIS])
        manifest_content = self._build_manifest(name, purpose, subais)
        manifest_path.write_text(manifest_content, encoding="utf-8")
        files_created.append(str(manifest_path))

        # evolution_log.yaml
        evo_path = dept_dir / "evolution_log.yaml"
        evo_path.write_text(
            f"# Evolution log for {name}\n"
            f"entries:\n"
            f'  - date: "auto"\n'
            f'    event: "Department {name} created by DAI.DepartmentGenerator"\n',
            encoding="utf-8",
        )
        files_created.append(str(evo_path))

        return {
            "department_dir": dept_dir,
            "files_created": files_created,
            "name": name,
            "purpose": purpose,
        }

    def _build_manifest(self, name: str, purpose: str, subais: List[str]) -> str:
        import yaml  # type: ignore

        manifest = {
            "name": name,
            "purpose": purpose,
            "version": "0.1.0",
            "subais": subais,
            "endpoints": [],
            "ux_panels": [],
            "ux_flows": [],
            "animations": [],
            "transitions": [],
            "3D_layers": [],
            "LG_layers": [],
        }
        return yaml.dump(manifest, default_flow_style=False, sort_keys=False)
