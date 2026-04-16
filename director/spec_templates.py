"""
spec_templates.py — Reusable patterns for subsystem specifications.

These templates are consumed by DirectorAI.generate_spec() to produce
consistent, well-structured SubsystemSpec instances.  They encode
architectural conventions — not business logic.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Responsibility patterns
# ---------------------------------------------------------------------------

RESPONSIBILITY_PATTERNS: dict[str, list[str]] = {
    "specialist_agent": [
        "Accept a typed request from the router.",
        "Execute domain-specific diagnostic / resolution logic.",
        "Return a typed response conforming to the shared schema.",
        "Log all decisions with structured evidence.",
        "Never raise — wrap errors in the response object.",
    ],
    "tool_adapter": [
        "Provide a uniform interface (ABC) for an external capability.",
        "Translate between internal data structures and provider SDKs.",
        "Handle authentication, retries, and rate limits internally.",
        "Return a typed result object — never raw provider payloads.",
        "Fail gracefully with an error field, not exceptions.",
    ],
    "data_layer": [
        "Persist and retrieve structured records.",
        "Enforce schema validation on write.",
        "Support versioned upsert (create-or-update).",
        "Expose query methods that return typed result sets.",
        "Isolate storage backend behind an abstract interface.",
    ],
    "http_service": [
        "Expose typed endpoints (request model → response model).",
        "Validate inputs at the boundary (reject bad data early).",
        "Delegate all business logic to internal modules — no logic in handlers.",
        "Return structured JSON errors with machine-readable codes.",
        "Serve static assets for any bundled UI.",
    ],
    "frontend": [
        "Present data from the backend in a clear, accessible layout.",
        "Validate inputs client-side before submission.",
        "Handle loading, success, and error states explicitly.",
        "Remain functional without JavaScript where possible (progressive enhancement).",
        "Communicate with the backend via a single API client module.",
    ],
}

# ---------------------------------------------------------------------------
# Contract patterns
# ---------------------------------------------------------------------------

CONTRACT_PATTERNS: dict[str, list[str]] = {
    "specialist_agent": [
        "MUST accept BaseRequest (or subclass) as sole input.",
        "MUST return BaseResponse (or subclass) — never None, never raise.",
        "MUST expose a `run(request) -> response` method.",
        "MUST set `response.error` on failure instead of raising.",
    ],
    "tool_adapter": [
        "MUST subclass the matching abstract interface (VisionInterface, WebInterface, etc.).",
        "MUST implement all abstract methods.",
        "MUST return the shared result dataclass, not raw provider output.",
        "Constructor MUST accept credentials explicitly — no hidden env reads.",
    ],
    "data_layer": [
        "MUST expose `save(record)`, `get(key)`, `query(filter)` at minimum.",
        "MUST validate records against the declared schema before writing.",
        "MUST be swappable (file, SQLite, Postgres) without changing callers.",
    ],
    "http_service": [
        "MUST use typed request/response models on every endpoint.",
        "MUST return JSON with a top-level `error` field on 4xx/5xx.",
        "MUST not import or instantiate business logic — use dependency injection.",
    ],
    "frontend": [
        "MUST call a single API_BASE URL — no hardcoded routes scattered in code.",
        "MUST display loading state while awaiting responses.",
        "MUST render errors from the backend `error` field, not generic messages.",
    ],
}

# ---------------------------------------------------------------------------
# Test idea patterns
# ---------------------------------------------------------------------------

TEST_PATTERNS: dict[str, list[str]] = {
    "specialist_agent": [
        "Unit: known-good input → expected diagnosis.",
        "Unit: empty / garbage input → graceful low-confidence response.",
        "Unit: every pattern in the pattern DB triggers at the right threshold.",
        "Integration: round-trip through router + agent + null tools.",
    ],
    "tool_adapter": [
        "Unit: mock the provider SDK — verify request shape and result mapping.",
        "Unit: provider returns error → result.error is set, no exception raised.",
        "Unit: missing credentials → clear RuntimeError at construction.",
        "Integration: live call with a real key (gated behind env flag).",
    ],
    "data_layer": [
        "Unit: save + get round-trip.",
        "Unit: upsert overwrites existing record.",
        "Unit: query with no matches returns empty list, not None.",
        "Unit: invalid schema on write → raises ValidationError.",
    ],
    "http_service": [
        "Unit: valid POST /diagnose → 200 + well-formed JSON.",
        "Unit: missing required field → 400 + error JSON.",
        "Unit: internal failure → 500 + error JSON (no stack trace in body).",
        "Integration: frontend → backend → agent → response.",
    ],
    "frontend": [
        "Manual: submit text-only → results render.",
        "Manual: submit image-only → results render.",
        "Manual: submit with no input → validation message.",
        "Manual: backend offline → error panel displays.",
    ],
}

# ---------------------------------------------------------------------------
# File layout patterns
# ---------------------------------------------------------------------------

FILE_LAYOUT_PATTERNS: dict[str, list[str]] = {
    "specialist_agent": [
        "director/specialists/{name}/__init__.py",
        "director/specialists/{name}/agent.py",
        "director/specialists/{name}/patterns.json",
        "director/specialists/{name}/decision_tree.md",
    ],
    "tool_adapter": [
        "director/tools/{category}/__init__.py",
        "director/tools/{category}/interface.py",
        "director/tools/{category}/{provider}.py",
    ],
    "data_layer": [
        "director/{name}/__init__.py",
        "director/{name}/interface.py",
        "director/{name}/store.py",
        "director/{name}/schema.py",
    ],
    "http_service": [
        "services/api/__init__.py",
        "services/api/server.py",
        "services/api/run.py",
    ],
    "frontend": [
        "ui/director/index.html",
        "ui/director/style.css",
        "ui/director/app.js",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_responsibilities(archetype: str) -> list[str]:
    return list(RESPONSIBILITY_PATTERNS.get(archetype, []))

def get_contracts(archetype: str) -> list[str]:
    return list(CONTRACT_PATTERNS.get(archetype, []))

def get_test_ideas(archetype: str) -> list[str]:
    return list(TEST_PATTERNS.get(archetype, []))

def get_file_layout(archetype: str, **fmt: str) -> list[str]:
    raw = FILE_LAYOUT_PATTERNS.get(archetype, [])
    return [f.format(**fmt) for f in raw]
