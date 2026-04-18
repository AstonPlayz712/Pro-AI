"""DAI.Generator — department, Sub-AI, backend, system-map, and UX generators."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from dai.core import Registry


def generate_department(
    name: str,
    *,
    registry: Optional[Registry] = None,
    base_dir: Path | str = ".",
    **ctx: Any,
) -> Dict[str, Any]:
    """Orchestrate full department generation: folder structure, Sub-AIs,
    backend endpoints, UX assets, system map, and registry entries.

    Returns a summary dict describing everything that was created.
    """
    from dai.generator.department_generator import DepartmentGenerator
    from dai.generator.subai_generator import SubAIGenerator
    from dai.generator.backend_generator import BackendGenerator
    from dai.generator.system_map_generator import SystemMapGenerator
    from dai.generator.ux_generator import UXGenerator

    reg = registry or Registry()
    base = Path(base_dir)

    # 1. Department scaffold
    dept_gen = DepartmentGenerator(registry=reg, base_dir=base)
    dept_result = dept_gen.generate(name, **ctx)

    # 2. Sub-AIs
    subai_gen = SubAIGenerator(registry=reg, base_dir=base)
    subai_result = subai_gen.generate(name, **ctx)

    # 3. Backend endpoints
    backend_gen = BackendGenerator(registry=reg, base_dir=base)
    backend_result = backend_gen.generate(name, **ctx)

    # 4. UX (panels, flows, animations, transitions, 3D, LG)
    ux_gen = UXGenerator(registry=reg, base_dir=base)
    ux_result = ux_gen.generate(name, **ctx)

    # 5. System map
    map_gen = SystemMapGenerator(registry=reg, base_dir=base)
    system_map_result = map_gen.generate(
        name,
        subais=subai_result["subais"],
        endpoints=backend_result["endpoints"],
        ux_panels=ux_result["panels"],
        ux_flows=ux_result["flows"],
        animations=ux_result["animations"],
        transitions=ux_result["transitions"],
        three_d_layers=ux_result["3d_layers"],
        lg_layers=ux_result["lg_layers"],
    )

    # 6. Register in global registry and save
    manifest = {
        "name": name,
        "purpose": ctx.get("purpose", f"{name} department"),
        "subais": subai_result["subais"],
        "endpoints": backend_result["endpoints"],
        "ux_panels": ux_result["panels"],
        "ux_flows": ux_result["flows"],
        "animations": ux_result["animations"],
        "transitions": ux_result["transitions"],
        "3D_layers": ux_result["3d_layers"],
        "LG_layers": ux_result["lg_layers"],
    }
    reg.register_department(name, manifest)
    reg.append_evolution(
        f"Generated department: {name} (Sub-AIs, backend, UX, 3D, LG)",
        "DAI.DepartmentGenerator",
    )
    reg.save()

    summary = {
        "department": name,
        "department_dir": str(dept_result["department_dir"]),
        "subais": subai_result["subais"],
        "endpoints": backend_result["endpoints"],
        "ux": ux_result,
        "system_map": str(system_map_result["path"]),
        "files_created": (
            dept_result["files_created"]
            + subai_result["files_created"]
            + backend_result["files_created"]
            + ux_result["files_created"]
            + system_map_result["files_created"]
        ),
    }

    _print_summary(summary)
    return summary


def _print_summary(summary: Dict[str, Any]) -> None:
    sep = "=" * 72
    print(sep)
    print(f" DAI.Ultra — Department Generated: {summary['department']}")
    print(sep)
    print(f"  Directory : {summary['department_dir']}")
    print(f"  Sub-AIs   : {', '.join(summary['subais'])}")
    print(f"  Endpoints : {len(summary['endpoints'])}")
    print(f"  UX Panels : {len(summary['ux'].get('panels', []))}")
    print(f"  UX Flows  : {len(summary['ux'].get('flows', []))}")
    print(f"  Animations: {len(summary['ux'].get('animations', []))}")
    print(f"  Transitions: {len(summary['ux'].get('transitions', []))}")
    print(f"  3D Layers : {len(summary['ux'].get('3d_layers', []))}")
    print(f"  LG Layers : {len(summary['ux'].get('lg_layers', []))}")
    print(f"  System Map: {summary['system_map']}")
    print(f"  Files     : {len(summary['files_created'])} total")
    print(sep)
    for f in summary["files_created"]:
        print(f"    + {f}")
    print(sep)
