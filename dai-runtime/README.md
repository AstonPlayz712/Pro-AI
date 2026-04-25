# DAI-Runtime

Cloud-hosted execution shell for **DAI — Director AI** of Dynamic SE.

> DAI orchestrates. It does not execute.
> DAI uses the **Perplexity Connector** as its execution engine.
> DAI-Runtime is **connector-first**: no API keys, no tokens, no env-var credentials.

This package is the L0 runtime that lets the strategic mind (DAI) reach
external surfaces. It lives alongside, **not inside**, the existing
`/dai/` (DAI.Ultra) and `/director/` packages so the strategic and runtime
concerns stay cleanly separated.

---

## How DAI works

```
            Daniela
               │
              DAI                  ← Level 3, strategic mind (this README's owner)
               │
   ┌───────────┴───────────┐
   ▼                       ▼
 DT (Sim)              BOS (Platform)
 8 depts · 14 sub-AIs  6 depts · 14 sub-AIs    (WIP — 1 seeded per dept)
   │                       │
   └────────►  L0 surfaces ◄────────┐
              Perplexity, Claude Desktop,
              Copilot, Slack, Monday, Asana
```

- DAI plans and decomposes work into Sub-AI tasks.
- Every Sub-AI call enters `core.run_subai(name, task)`.
- If the Sub-AI's connector is `perplexity`, the call funnels through
  `core.perplexity_query()` — which itself dispatches through the
  host's Perplexity Connector.
- Anything else is forwarded to `router.route_task()`.
- **All** outbound calls — Perplexity included — leave through the
  single external-connector dispatcher registered by the host.

---

## File layout

```
dai-runtime/
├── core.py              # perplexity_query(), run_subai(), config, errors
├── router.py            # route_task() and per-connector handlers
├── system_prompt.txt    # canonical DAI system prompt (loaded by core)
├── subai_registry.json  # list of Sub-AIs, connectors, channels, boards
├── connectors.json      # connector endpoints, auth, request shapes
└── README.md            # you are here
```

---

## Setup

DAI-Runtime has no API keys to configure. The host application owns all
credentials and exposes them as connectors. Bootstrap looks like this:

```python
from dai_runtime.core import set_external_connector_dispatcher

def my_dispatcher(connector_id: str, action: str, payload: dict) -> str:
    """Route to the host's connector surface and return text."""
    # e.g. forward to Perplexity Connectors / MCP / VS Code bridge
    ...

set_external_connector_dispatcher(my_dispatcher)
```

Supported `connector_id` values (declared in `connectors.json`):
`perplexity`, `claude_desktop`, `github_copilot`, `slack_direct`,
`monday`, `asana_mcp_merge`.

Until a dispatcher is registered, every outbound call raises
`DAIRuntimeError` — by design, so missing wiring is visible.

---

## Quick start

```python
from dai_runtime.core import perplexity_query, run_subai

# Direct reasoning call
print(perplexity_query("Draft a one-paragraph mission for DT."))

# Dispatch through a Sub-AI
print(run_subai("Silicon AI", "Propose a baseline 2026 mid-tier SoC spec."))
```

---

## How routing works

`router.route_task(subai_name, task)`:

1. Loads `subai_registry.json` and finds the matching Sub-AI record.
2. Reads the `connector` field on that record.
3. Looks the connector up in `connectors.json` for endpoint, auth, and
   request shape.
4. Calls the matching handler (`_handle_perplexity`, `_handle_slack`, …).
5. Returns the connector's textual response. Errors raise
   `DAIRuntimeError`.

Routing is deterministic. The router never makes autonomy decisions — it
forwards. Decisions live in DAI's plan, which is composed in Perplexity
through `core.perplexity_query`.

---

## How connectors work

Connectors are L0 — no autonomy, act only on packets. Every entry in
`connectors.json` is `kind: external_connector` and declares only its
`connector_id`, `action`, and `request_shape`. Authentication is the
host's responsibility.

| Key             | connector_id        | action             | Auth     |
|-----------------|---------------------|--------------------|----------|
| `perplexity`    | `perplexity`        | `chat_completions` | host     |
| `claude_desktop`| `claude_desktop`    | `messages`         | host     |
| `copilot`       | `github_copilot`    | `chat`             | host     |
| `slack`         | `slack_direct`      | `post_message`     | host     |
| `monday`        | `monday`            | `create_item`      | host     |
| `asana`         | `asana_mcp_merge`   | `create_task`      | host     |

Adding a new connector means: (a) add an entry to `connectors.json`,
(b) add a `_handle_<key>` function to `router.py`, (c) register it in
the `_HANDLERS` dict, (d) ensure the host dispatcher recognises the new
`connector_id`.

---

## How to add new Sub-AIs

1. Open `subai_registry.json`.
2. Append a record with these fields:

   ```json
   {
     "name": "Pricing AI",
     "department": "DT-4 Market",
     "connector": "perplexity",
     "system_prompt": "You are Pricing AI, a Sub-AI under DT Market...",
     "slack_channel": "#dt-market",
     "monday_board": "",
     "asana_project": ""
   }
   ```

3. Confirm the record passes the global density rule:
   - ≤ 4 sub-AIs per department
   - ≤ 40 sub-AIs per project
4. Open a PR. Structural changes require Daniela's approval.

---

## Maintaining DAI through VS Code

DAI-Runtime is designed to be edited in **VS Code Insiders** with
GitHub Copilot Chat or Claude Code as the editing surface — both are
L0 from DAI's perspective.

Suggested loop:

1. Ask Copilot Chat or Claude Code to draft an edit (registry entry,
   handler, system-prompt revision).
2. Review the diff in the VS Code source-control view.
3. Run a smoke test:
   ```python
   from dai_runtime.core import perplexity_query
   perplexity_query("ping")
   ```
4. Commit on a feature branch and open a PR.

Never edit `system_prompt.txt` casually — it is the canonical voice of
DAI. Treat it like a doctrine file, not a config file.

---

## Doctrine

- **Orchestrate, don't execute.** This runtime exists so DAI can dispatch
  without leaving its strategic seat.
- **Strict autonomy boundaries.** L3 DAI · L2 Agents · L1 Sub-AIs ·
  L0 surfaces (everything in `connectors.json`).
- **Density.** 6–10 departments, 3–4 sub-AIs each, 20–40 sub-AIs per
  project, ≤ 8 visible UI elements.
- **Escalate.** Any structural change, any density breach, any
  cross-pillar conflict, any blocking L0 failure goes to Daniela.

---

## Status

- Version: 0.1.0 (WIP)
- Last structural change: initial scaffold — DT (8 depts · 8 seeded
  sub-AIs) and BOS (6 depts · 6 seeded sub-AIs).
- Reserved slots: 32, empty pending Daniela's approval.
