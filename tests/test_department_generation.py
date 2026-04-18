"""Tests for DAI.Ultra Department Generation subsystem.

Validates that generate_department creates the expected folder structure,
system maps, UX assets, backend endpoints, and registry entries.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml  # type: ignore

from dai.core import Registry


@pytest.fixture()
def workspace(tmp_path: Path):
    """Create a minimal workspace with a system_map.yaml so generators can run."""
    dai_dir = tmp_path / "dai"
    dai_dir.mkdir()
    (dai_dir / "departments").mkdir()

    # Seed a minimal system_map.yaml
    system_map = {
        "version": "0.1.0",
        "dai_modules": {},
        "departments": {},
        "endpoints": {},
        "ux_panels": {},
        "evolution_log": [],
    }
    map_path = dai_dir / "system_map.yaml"
    map_path.write_text(yaml.dump(system_map), encoding="utf-8")

    return tmp_path, map_path


class TestDepartmentGeneration:
    """End-to-end test: generate a department and verify outputs."""

    def test_full_generation(self, workspace):
        tmp_path, map_path = workspace
        from dai.generator import generate_department

        registry = Registry(path=map_path)
        result = generate_department("TestDept", registry=registry, base_dir=tmp_path)

        # -- Department folder created --
        dept_dir = tmp_path / "dai" / "departments" / "testdept"
        assert dept_dir.is_dir()
        assert (dept_dir / "__init__.py").exists()
        assert (dept_dir / "manifest.yaml").exists()

        # -- System map is valid YAML --
        sm_path = dept_dir / "system_map.yaml"
        assert sm_path.exists()
        sm = yaml.safe_load(sm_path.read_text(encoding="utf-8"))
        assert sm["department"] == "TestDept"
        assert "subais" in sm
        assert "endpoints" in sm
        assert "ux_panels" in sm
        assert "3D_layers" in sm
        assert "LG_layers" in sm

        # -- UX folders exist --
        ux_root = tmp_path / "ux" / "testdept"
        assert ux_root.is_dir()
        assert (ux_root / "flows").is_dir()
        assert (ux_root / "animations").is_dir()
        assert (ux_root / "transitions").is_dir()
        assert (ux_root / "3d").is_dir()
        assert (ux_root / "lg").is_dir()

        # -- UX JSON files are valid --
        panels = json.loads((ux_root / "panels.json").read_text(encoding="utf-8"))
        assert "panels" in panels
        assert len(panels["panels"]) > 0

        flows = json.loads((ux_root / "flows" / "flows.json").read_text(encoding="utf-8"))
        assert "flows" in flows

        anims = json.loads((ux_root / "animations" / "animations.json").read_text(encoding="utf-8"))
        assert "animations" in anims
        assert "easing_curves" in anims
        assert "micro_interactions" in anims

        trans = json.loads((ux_root / "transitions" / "transitions.json").read_text(encoding="utf-8"))
        assert "screen_transitions" in trans
        assert "state_transitions" in trans

        three_d = json.loads((ux_root / "3d" / "3d_layers.json").read_text(encoding="utf-8"))
        assert "elevation_rules" in three_d
        assert "parallax_rules" in three_d
        assert len(three_d["layers"]) > 0

        lg = json.loads((ux_root / "lg" / "lg_layers.json").read_text(encoding="utf-8"))
        assert "blur_refraction_rules" in lg
        assert "lg_global" in lg
        assert len(lg["layers"]) > 0

        # -- Backend endpoints load --
        api_dir = tmp_path / "api" / "testdept"
        assert api_dir.is_dir()
        assert (api_dir / "router.py").exists()
        assert (api_dir / "register.py").exists()

        # -- Registry entries correct --
        reg_data = registry.load()
        assert "TestDept" in reg_data["departments"]
        dept_entry = reg_data["departments"]["TestDept"]
        assert len(dept_entry["subais"]) > 0
        assert len(dept_entry["endpoints"]) > 0
        assert len(dept_entry["ux_panels"]) > 0
        assert len(dept_entry["animations"]) > 0
        assert len(dept_entry["3D_layers"]) > 0
        assert len(dept_entry["LG_layers"]) > 0

    def test_subai_files_created(self, workspace):
        tmp_path, map_path = workspace
        from dai.generator.subai_generator import SubAIGenerator

        registry = Registry(path=map_path)
        gen = SubAIGenerator(registry=registry, base_dir=tmp_path)
        result = gen.generate("BuilderOS")

        subais_dir = tmp_path / "dai" / "departments" / "builderos" / "subais"
        assert subais_dir.is_dir()
        assert (subais_dir / "subai_planner.py").exists()
        assert (subais_dir / "subai_executor.py").exists()
        assert (subais_dir / "subai_monitor.py").exists()
        assert len(result["subais"]) == 3

    def test_backend_router_syntax(self, workspace):
        tmp_path, map_path = workspace
        from dai.generator.backend_generator import BackendGenerator

        registry = Registry(path=map_path)
        gen = BackendGenerator(registry=registry, base_dir=tmp_path)
        result = gen.generate("Auto")

        router_path = tmp_path / "api" / "auto" / "router.py"
        assert router_path.exists()
        source = router_path.read_text(encoding="utf-8")
        assert "APIRouter" in source
        assert "/api/auto" in source
        assert "async def get_status" in source
        assert "async def post_command" in source
        assert "async def post_ux_event" in source
        assert "async def list_subais" in source

    def test_multiple_departments(self, workspace):
        tmp_path, map_path = workspace
        from dai.generator import generate_department

        registry = Registry(path=map_path)
        for name in ["BuilderOS", "Auto", "ITS"]:
            generate_department(name, registry=registry, base_dir=tmp_path)

        reg_data = registry.load()
        assert "BuilderOS" in reg_data["departments"]
        assert "Auto" in reg_data["departments"]
        assert "ITS" in reg_data["departments"]

    def test_evolution_log_appended(self, workspace):
        tmp_path, map_path = workspace
        from dai.generator import generate_department

        registry = Registry(path=map_path)
        generate_department("ITS", registry=registry, base_dir=tmp_path)

        reg_data = registry.load()
        log = reg_data.get("evolution_log", [])
        assert any("ITS" in entry.get("change", "") for entry in log)
