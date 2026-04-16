"""DAI.SystemMapGenerator — generate per-department system_map.yaml files."""
from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, List

from dai.core import Registry


class SystemMapGenerator:
    """Creates a system_map.yaml for a department with full topology."""

    def __init__(self, *, registry: Registry, base_dir: Path) -> None:
        self.registry = registry
        self.base = base_dir

    def generate(
        self,
        dept_name: str,
        *,
        subais: List[str] | None = None,
        endpoints: List[Dict[str, str]] | None = None,
        ux_panels: List[str] | None = None,
        ux_flows: List[str] | None = None,
        animations: List[str] | None = None,
        transitions: List[str] | None = None,
        three_d_layers: List[str] | None = None,
        lg_layers: List[str] | None = None,
    ) -> Dict[str, Any]:
        import yaml  # type: ignore

        dept_dir = self.base / "dai" / "departments" / dept_name.lower()
        dept_dir.mkdir(parents=True, exist_ok=True)

        system_map = {
            "department": dept_name,
            "version": "0.1.0",
            "generated_by": "DAI.SystemMapGenerator",
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "subais": subais or [],
            "endpoints": [
                {"method": ep["method"], "path": ep["path"]}
                for ep in (endpoints or [])
            ],
            "ux_panels": ux_panels or [],
            "ux_flows": ux_flows or [],
            "animations": animations or [],
            "transitions": transitions or [],
            "3D_layers": three_d_layers or [],
            "LG_layers": lg_layers or [],
            "evolution_history": [
                {
                    "date": datetime.date.today().isoformat(),
                    "event": f"Initial generation of {dept_name} system map",
                    "author": "DAI.SystemMapGenerator",
                },
            ],
        }

        map_path = dept_dir / "system_map.yaml"
        map_path.write_text(
            yaml.dump(system_map, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

        return {
            "path": map_path,
            "files_created": [str(map_path)],
        }
