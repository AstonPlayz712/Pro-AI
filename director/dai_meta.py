"""
dai_meta.py — Director-AI v1: the meta-architect.

DAI-v1 does NOT diagnose problems.  It DESIGNS and COMMISSIONS subsystems.

Capabilities
------------
- List the subsystems that should exist in the Pro-AI ecosystem.
- Generate a full SubsystemSpec for any subsystem.
- Generate a Claude Code prompt that would implement a subsystem from spec.
- Maintain a persistent system_map.yaml registry of commissioned subsystems.
- Propose the next unit of work based on current registry state.

Usage
-----
    from director.dai_meta import DirectorAI

    dai = DirectorAI()
    spec = dai.generate_spec("its_mac_boot")
    prompt = dai.generate_cc_prompt("its_mac_boot", spec)
    dai.update_system_map(spec)
    print(dai.plan_next_work())
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from director.spec_templates import (
    get_responsibilities,
    get_contracts,
    get_test_ideas,
    get_file_layout,
)

_MAP_PATH = Path(__file__).parent / "system_map.yaml"


# ═══════════════════════════════════════════════════════════════════════════
# Data structures
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SubsystemSpec:
    name:             str
    version:          str              = "0.1.0"
    purpose:          str              = ""
    responsibilities: list[str]        = field(default_factory=list)
    inputs:           list[str]        = field(default_factory=list)
    outputs:          list[str]        = field(default_factory=list)
    files:            list[str]        = field(default_factory=list)
    contracts:        list[str]        = field(default_factory=list)
    test_ideas:       list[str]        = field(default_factory=list)
    dependencies:     list[str]        = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SystemMap:
    subsystems: dict[str, dict[str, Any]] = field(default_factory=dict)

    # -- persistence --------------------------------------------------------

    @classmethod
    def load(cls, path: Path = _MAP_PATH) -> "SystemMap":
        if not path.exists():
            return cls()
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls(subsystems=raw.get("subsystems") or {})

    def save(self, path: Path = _MAP_PATH) -> None:
        path.write_text(
            yaml.dump(
                {"subsystems": self.subsystems},
                default_flow_style=False,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    # -- queries ------------------------------------------------------------

    def registered(self) -> list[str]:
        return list(self.subsystems.keys())

    def is_registered(self, name: str) -> bool:
        return name in self.subsystems

    def get_version(self, name: str) -> str | None:
        entry = self.subsystems.get(name)
        return entry.get("version") if entry else None


# ═══════════════════════════════════════════════════════════════════════════
# DirectorAI — the meta-architect
# ═══════════════════════════════════════════════════════════════════════════

class DirectorAI:
    """
    Architect that designs and commissions all Pro-AI subsystems.

    It never implements business logic — it produces *specifications*
    and *Claude Code prompts* that describe what needs to be built.
    """

    # Canonical ordering: each tuple is (name, archetype).
    # Archetype maps to template patterns in spec_templates.py.
    SUBSYSTEMS: list[tuple[str, str]] = [
        ("its_mac_boot",  "specialist_agent"),
        ("tool_factory",  "tool_adapter"),
        ("memory_layer",  "data_layer"),
        ("backend",       "http_service"),
        ("ux",            "frontend"),
    ]

    def __init__(self, map_path: Path = _MAP_PATH) -> None:
        self._map_path = map_path
        self._system_map = SystemMap.load(map_path)
        self._spec_registry: dict[str, Callable[[], SubsystemSpec]] = {
            "its_mac_boot":  self._spec_its_mac_boot,
            "tool_factory":  self._spec_tool_factory,
            "memory_layer":  self._spec_memory_layer,
            "backend":       self._spec_backend,
            "ux":            self._spec_ux,
        }

    # ── public API ─────────────────────────────────────────────────────

    def list_subsystems(self) -> list[str]:
        """Return canonical subsystem names in dependency order."""
        return [name for name, _ in self.SUBSYSTEMS]

    def plan_next_work(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Propose the next subsystem to build or evolve.

        Logic (intentionally simple for v1):
          1. Walk SUBSYSTEMS in order.
          2. First one not yet in system_map → "create".
          3. If all exist, first one whose version < latest spec version → "evolve".
          4. If everything is current → "idle".
        """
        context = context or {}
        for name, _ in self.SUBSYSTEMS:
            if not self._system_map.is_registered(name):
                spec = self.generate_spec(name)
                return {
                    "action":    "create",
                    "subsystem": name,
                    "spec":      spec.to_dict(),
                    "reason":    f"{name} has not been commissioned yet.",
                }

        for name, _ in self.SUBSYSTEMS:
            current = self._system_map.get_version(name)
            latest  = self.generate_spec(name).version
            if current != latest:
                spec = self.generate_spec(name)
                return {
                    "action":        "evolve",
                    "subsystem":     name,
                    "from_version":  current,
                    "to_version":    latest,
                    "spec":          spec.to_dict(),
                    "reason":        f"{name} is at {current}, latest spec is {latest}.",
                }

        return {
            "action":  "idle",
            "reason":  "All subsystems are commissioned and up-to-date.",
        }

    def generate_spec(self, subsystem_name: str) -> SubsystemSpec:
        """Generate a full SubsystemSpec for the named subsystem."""
        factory = self._spec_registry.get(subsystem_name)
        if factory is None:
            raise ValueError(
                f"Unknown subsystem: {subsystem_name!r}. "
                f"Known: {list(self._spec_registry.keys())}"
            )
        return factory()

    def generate_cc_prompt(
        self,
        subsystem_name: str,
        spec: SubsystemSpec,
    ) -> str:
        """Render a Claude Code implementation prompt from a spec."""
        return self._render_cc_prompt(subsystem_name, spec)

    def update_system_map(self, spec: SubsystemSpec) -> None:
        """Register (or update) a subsystem in the persistent system_map."""
        self._system_map.subsystems[spec.name] = {
            "version":        spec.version,
            "purpose":        spec.purpose,
            "file_count":     len(spec.files),
            "files":          spec.files,
            "commissioned_at": datetime.now(timezone.utc).isoformat(),
        }
        self._system_map.save(self._map_path)

    # ── internal spec generators ───────────────────────────────────────

    def _spec_its_mac_boot(self) -> SubsystemSpec:
        arch = "specialist_agent"
        return SubsystemSpec(
            name="its_mac_boot",
            version="0.2.0",
            purpose=(
                "Diagnose MacBook Pro 2010 boot failures by matching symptoms "
                "against a curated pattern database.  Produces a ranked list of "
                "findings with confidence scores, root-cause analysis, repair "
                "steps, and parts lists."
            ),
            responsibilities=[
                *get_responsibilities(arch),
                "Score each pattern in patterns.json against combined text + vision signals.",
                "Select the top-N findings above a configurable threshold.",
                "Optionally enrich the top finding with a live web search.",
                "Support both text-only and image-assisted (vision OCR) input.",
            ],
            inputs=[
                "DAIRequest.raw_text — free-text problem description.",
                "DAIRequest.image_paths — zero or more screen/photo paths.",
                "DAIRequest.context.device_model — e.g. 'MacBook Pro 2010 13-inch'.",
                "DAIRequest.context.symptom_tags — optional keyword list.",
            ],
            outputs=[
                "ITSResponse.summary — one-sentence diagnosis.",
                "ITSResponse.confidence — float 0..1.",
                "ITSResponse.severity — low | medium | high | critical.",
                "ITSResponse.root_cause — explanation of the underlying failure.",
                "ITSResponse.findings — ranked ITSFinding list with evidence.",
                "ITSResponse.repair_steps — ordered action list.",
                "ITSResponse.parts_needed — part numbers / descriptions.",
                "ITSResponse.references — URLs to guides and discussions.",
            ],
            files=get_file_layout(arch, name="its_mac_boot"),
            contracts=[
                *get_contracts(arch),
                "MUST load patterns from patterns.json at init (not per-request).",
                "MUST coerce a plain DAIRequest to ITSRequest transparently.",
            ],
            test_ideas=[
                *get_test_ideas(arch),
                "Unit: 'flashing folder question mark' → P001 with score >= 0.20.",
                "Unit: 'kernel panic AppleAHCIPort' → P002.",
                "Unit: 'clicking grinding' → P005 with severity CRITICAL.",
                "Unit: unrelated input ('printer jam') → no match, low confidence.",
            ],
            dependencies=["tool_factory"],
        )

    def _spec_tool_factory(self) -> SubsystemSpec:
        arch = "tool_adapter"
        return SubsystemSpec(
            name="tool_factory",
            version="0.2.0",
            purpose=(
                "Provide a unified factory that selects and constructs the "
                "best available vision and web-search backends based on "
                "environment credentials.  Each backend conforms to a shared "
                "abstract interface so callers never depend on a specific provider."
            ),
            responsibilities=[
                *get_responsibilities(arch),
                "Read API keys from environment / .env via core.config.",
                "Select vision backend: Anthropic → OpenAI → Gemini → Null.",
                "Select web backend: Google CSE → Brave → DuckDuckGo.",
                "Expose create_vision_tool() and create_web_tool() at module level.",
            ],
            inputs=[
                "Environment variables: ANTHROPIC_API_KEY, OPENAI_API_KEY, "
                "GOOGLE_API_KEY, GOOGLE_CSE_ID, BRAVE_API_KEY.",
                "Optional model overrides: ANTHROPIC_MODEL, OPENAI_MODEL, GEMINI_MODEL.",
            ],
            outputs=[
                "VisionInterface instance (describe + ocr methods).",
                "WebInterface instance (search + fetch methods).",
            ],
            files=[
                "core/config.py",
                *get_file_layout(arch, category="vision", provider="claude_vision"),
                *get_file_layout(arch, category="vision", provider="openai_vision"),
                *get_file_layout(arch, category="vision", provider="gemini_vision"),
                *get_file_layout(arch, category="web", provider="google_web"),
                *get_file_layout(arch, category="web", provider="brave_web"),
                *get_file_layout(arch, category="web", provider="ddg_web"),
            ],
            contracts=[
                *get_contracts(arch),
                "create_vision_tool(cfg?) MUST return a usable VisionInterface — never None.",
                "create_web_tool(cfg?) MUST return a usable WebInterface — never None.",
                "Null implementations MUST be returned when no keys are present (no crash).",
            ],
            test_ideas=[
                *get_test_ideas(arch),
                "Unit: no env keys → NullVisionInterface + DuckDuckGoWebInterface.",
                "Unit: only ANTHROPIC_API_KEY → ClaudeVisionInterface.",
                "Unit: only BRAVE_API_KEY → BraveWebInterface.",
                "Unit: GOOGLE_API_KEY without CSE_ID → Gemini vision, DuckDuckGo web.",
            ],
            dependencies=[],
        )

    def _spec_memory_layer(self) -> SubsystemSpec:
        arch = "data_layer"
        return SubsystemSpec(
            name="memory_layer",
            version="0.1.0",
            purpose=(
                "Persist diagnostic history, user preferences, and learned "
                "patterns across sessions.  The memory layer stores structured "
                "records behind an abstract interface so the storage engine "
                "(JSON files, SQLite, Postgres) can be swapped without "
                "affecting callers."
            ),
            responsibilities=[
                *get_responsibilities(arch),
                "Store completed DAIResponse records keyed by request_id.",
                "Store user-tagged notes, corrections, and feedback.",
                "Support keyword search across past diagnoses.",
                "Track per-pattern hit frequency for adaptive scoring.",
            ],
            inputs=[
                "DAIResponse (or subclass) after a completed diagnosis.",
                "UserNote: free-text annotation attached to a request_id.",
                "QueryFilter: keyword, date range, domain filter.",
            ],
            outputs=[
                "DiagnosisRecord — enriched DAIResponse + metadata.",
                "list[DiagnosisRecord] from query.",
                "PatternStats — per-pattern hit counts and average scores.",
            ],
            files=get_file_layout(arch, name="memory"),
            contracts=[
                *get_contracts(arch),
                "MUST never lose data on process crash (flush after every write).",
                "MUST support atomic upsert: save() on an existing key overwrites.",
            ],
            test_ideas=[
                *get_test_ideas(arch),
                "Unit: save a DiagnosisRecord, get by request_id → identical.",
                "Unit: query by domain 'its_mac_boot' returns only ITS records.",
                "Unit: pattern stats reflect cumulative saves.",
            ],
            dependencies=["tool_factory"],
        )

    def _spec_backend(self) -> SubsystemSpec:
        arch = "http_service"
        return SubsystemSpec(
            name="backend",
            version="0.2.0",
            purpose=(
                "HTTP service layer (FastAPI) that exposes Director-AI "
                "capabilities as a REST API.  Handles multipart uploads, "
                "input validation, CORS, and static UI serving.  Contains "
                "zero business logic — all work is delegated to internal modules."
            ),
            responsibilities=[
                *get_responsibilities(arch),
                "POST /diagnose — accept text + images, call DirectorAI.handle(), return JSON.",
                "GET /config — report active backends (no secrets).",
                "GET /health — liveness probe.",
                "Serve ui/director/ as static files at /ui.",
                "Persist uploaded images to a configurable upload directory.",
            ],
            inputs=[
                "multipart/form-data with fields: text, device_model, images[].",
            ],
            outputs=[
                "JSON DAIResponse on 200.",
                "JSON {error: string} on 4xx / 5xx.",
            ],
            files=get_file_layout(arch),
            contracts=[
                *get_contracts(arch),
                "MUST reject uploads exceeding DAI_MAX_UPLOAD_BYTES with HTTP 413.",
                "MUST NOT import specialist agents directly — go through DirectorAI.",
            ],
            test_ideas=[
                *get_test_ideas(arch),
                "Unit: POST /diagnose with valid text → 200 + domain field present.",
                "Unit: POST /diagnose with no body → 400.",
                "Unit: GET /health → 200 {status: 'ok'}.",
                "Unit: oversized upload → 413.",
            ],
            dependencies=["tool_factory", "its_mac_boot"],
        )

    def _spec_ux(self) -> SubsystemSpec:
        arch = "frontend"
        return SubsystemSpec(
            name="ux",
            version="0.2.0",
            purpose=(
                "Single-page frontend (vanilla HTML/CSS/JS) that provides "
                "a diagnostic interface for Director-AI.  Text input, image "
                "upload with drag-and-drop, a Diagnose button, and a results "
                "panel that renders the full DAIResponse."
            ),
            responsibilities=[
                *get_responsibilities(arch),
                "Text input for problem description.",
                "Device-model input (optional).",
                "Image upload area with drag-and-drop and thumbnail previews.",
                "'Diagnose' button that POSTs to /diagnose.",
                "Results panel: domain, confidence, severity, summary, evidence, actions, parts, references.",
                "Raw JSON expandable section for debugging.",
                "Status bar showing active vision/web backends (from GET /config).",
            ],
            inputs=[
                "User-typed text.",
                "User-uploaded images (drag-and-drop or file picker).",
            ],
            outputs=[
                "Rendered DAIResponse in structured panels.",
                "Raw JSON for debugging.",
            ],
            files=get_file_layout(arch),
            contracts=[
                *get_contracts(arch),
                "MUST work when served by FastAPI at /ui and when opened as file://.",
                "MUST degrade gracefully: if backend is offline, show a clear error.",
            ],
            test_ideas=[
                *get_test_ideas(arch),
                "Manual: type 'MacBook flashing folder' + click Diagnose → results appear.",
                "Manual: drag a PNG into the upload area → thumbnail renders.",
                "Manual: stop backend → submit → error panel visible.",
            ],
            dependencies=["backend"],
        )

    # ── prompt renderer ────────────────────────────────────────────────

    @staticmethod
    def _render_cc_prompt(subsystem_name: str, spec: SubsystemSpec) -> str:
        """Render a complete Claude Code prompt for implementing a subsystem."""

        files_block = "\n".join(f"  - {f}" for f in spec.files)
        resp_block  = "\n".join(f"  - {r}" for r in spec.responsibilities)
        input_block = "\n".join(f"  - {i}" for i in spec.inputs)
        out_block   = "\n".join(f"  - {o}" for o in spec.outputs)
        contract_block = "\n".join(f"  - {c}" for c in spec.contracts)
        test_block  = "\n".join(f"  - {t}" for t in spec.test_ideas)
        dep_block   = "\n".join(f"  - {d}" for d in spec.dependencies) if spec.dependencies else "  (none)"

        return textwrap.dedent(f"""\
            You are the Lead Engineer AI for the Pro-AI repository.

            Generate the **{spec.name}** subsystem (v{spec.version}).

            ## Purpose

            {spec.purpose}

            ## Files to create

            {files_block}

            ## Responsibilities

            {resp_block}

            ## Inputs

            {input_block}

            ## Outputs

            {out_block}

            ## Contracts / invariants

            {contract_block}

            ## Test ideas

            {test_block}

            ## Dependencies

            {dep_block}

            ## Requirements

            - Code must be clean, typed (Python 3.11+ style), and modular.
            - Each file must be importable standalone.
            - Follow existing project conventions (dataclasses, ABCs, structured logging).
            - Do not stub or leave TODO placeholders — implement fully.
            - Do not ask questions. Generate all code.
        """)


# ═══════════════════════════════════════════════════════════════════════════
# Standalone entry-point
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Demo: generate all specs and prompts, print a work plan."""
    import json

    dai = DirectorAI()

    print("=" * 72)
    print("DAI-v1 Meta-Architect -- Subsystem Inventory")
    print("=" * 72)

    for name in dai.list_subsystems():
        spec   = dai.generate_spec(name)
        prompt = dai.generate_cc_prompt(name, spec)
        registered = dai._system_map.is_registered(name)
        status = f"v{dai._system_map.get_version(name)}" if registered else "NOT REGISTERED"

        print(f"\n{'-' * 72}")
        print(f"  Subsystem : {spec.name}")
        print(f"  Version   : {spec.version}")
        print(f"  Status    : {status}")
        print(f"  Purpose   : {spec.purpose[:100]}...")
        print(f"  Files     : {len(spec.files)}")
        print(f"  Tests     : {len(spec.test_ideas)}")
        print(f"  Prompt    : {len(prompt)} chars")

    print(f"\n{'=' * 72}")
    print("Next work:")
    plan = dai.plan_next_work()
    print(json.dumps(plan, indent=2, default=str))


if __name__ == "__main__":
    main()
