# DAI.Ultra

Recursive, self-expanding multi-agent architecture designer.

## Layout

```
dai/
├── __init__.py
├── system_map.yaml              # single source of truth
├── core.py                      # DesignSpec, PAModeSpec, Registry, Director
├── agents/
│   ├── subsystem_architect.py   # DAI.SubsystemArchitect
│   ├── pa_architect.py          # DAI.PAArchitect
│   ├── code_architect.py        # DAI.CodeArchitect
│   ├── ux_architect.py          # DAI.UXArchitect
│   ├── backend_architect.py     # DAI.BackendArchitect
│   ├── test_architect.py        # DAI.TestArchitect
│   ├── doc_architect.py         # DAI.DocArchitect
│   └── self_architect.py        # DAI.SelfArchitect (evolves system_map)
└── pa_modes/
    └── CheckDisk.yaml           # example PAModeSpec
```

## Workflow

1. User asks DAI.Ultra to design something.
2. Director dispatches to the matching architect.
3. Architect emits a `DesignSpec` (or `PAModeSpec` for PA modes).
4. `DAI.SelfArchitect` patches `system_map.yaml` via `system_map_patch`.
5. `DAI.CodeArchitect` hands file stubs to Claude Code for real generation.

## Next increments

- Implement `Registry.load/save` against `system_map.yaml` (PyYAML).
- Implement `PAArchitect.design_mode` to emit real `PAModeSpec` objects.
- Wire `Director.evolve` → `SelfArchitect.apply` + evolution_log append.
- Add the first real helper: `scripts/pa/check_disk.ps1`.
- Add `DAI.TestArchitect` harness that converts `test_ideas` → pytest cases.
```
