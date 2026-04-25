# DM — Device Maker (DM-Full v1)

> **Status:** WIP — structural skeleton only.
> The seven DM Sub-AIs have not yet produced their first packets. Every
> code-bearing folder in this tree contains an `AWAITING.md` placeholder
> until DAI dispatches the corresponding mind.

## What DM is

DM (**Device Maker**) is the Device Tycoon department responsible for the
end-user-facing studio: pick components → assemble a device → validate
against realism → score against the market → save / iterate.

DM is one department under the **DT** pillar. It is bounded by Dynamic SE's
density rule (≤ 4 sub-AIs per dept at full expansion; here we run the
seven the directive named, which exceeds the standard cap and is therefore
flagged for DAI review — see `Open structural questions` below).

## Independent minds in this department

| Sub-AI | Domain (one line) | Signature surface |
|---|---|---|
| **DM-Logic**    | Core simulation and rules logic                 | `/dm/.subai/dm-logic.prompt.md`    |
| **DM-UI**       | Screens, widgets, layout, visual hierarchy      | `/dm/.subai/dm-ui.prompt.md`       |
| **DM-UX**       | Flows, interaction, micro-feedback              | `/dm/.subai/dm-ux.prompt.md`       |
| **DM-Realism**  | Physical / electrical / thermal / cost realism  | `/dm/.subai/dm-realism.prompt.md`  |
| **DM-Market**   | Consumer segments, demand, competitor response  | `/dm/.subai/dm-market.prompt.md`   |
| **DM-Reviewer** | Cross-Sub-AI audit, density gate                | `/dm/.subai/dm-reviewer.prompt.md` |
| **DM-Auto**     | Headless harness, batch sweeps, CI hooks        | `/dm/.subai/dm-auto.prompt.md`     |

Each prompt file is a **dispatch surface**, not a finished system prompt.
DAI is the only entity that may modify or expand them.

## Folder layout

```
dm/
├── README.md           ← this file
├── .subai/             ← Sub-AI signature surfaces (one prompt per mind)
├── logic/              ← AWAITING DM-Logic, DM-Realism, DM-Market, DM-Auto
├── ui/                 ← AWAITING DM-UI, DM-UX
├── app/                ← AWAITING app-shell owner (assigned by DAI)
└── assets/             ← AWAITING reference device
```

## How dispatch works (executor view)

1. **DAI** authors a packet for one of the seven Sub-AIs.
2. The Sub-AI returns file content and a target path under `/dm/`.
3. The **executor** (this surface) writes the file verbatim and commits.
4. **DM-Reviewer** runs an audit pass when a release candidate exists.
5. Conflicts and density-rule breaches escalate to **DAI**.

The executor never invents module names, framework choices, segmentation
schemes, screens, flows, or constraint values. Those decisions belong
to the Sub-AIs.

## Connector-first guarantee

DM-Full v1 is built on the **connector-first** runtime introduced in
PR #12 (`dai-runtime/`). No file in `/dm/` may hard-code an API key,
bearer token, env-var credential, or HTTP endpoint that bypasses the
host's external-connector dispatcher. Reasoning calls funnel through
`dai_runtime.core.perplexity_query`; non-Perplexity calls go through
`dai_runtime.router.route_task`.

## Open structural questions (for DAI / Daniela)

1. **Headcount cap.** The standard density rule is 3–4 sub-AIs per dept.
   DM has been seeded with **7**. This is an explicit override — please
   confirm it is intentional or instruct a merge (e.g. fold DM-Reviewer
   under DM-Auto, or treat DM-Realism as a constraint module under
   DM-Logic).
2. **App-shell ownership.** `/dm/app/` has no default owner. DAI should
   name one of the seven before first dispatch.
3. **Framework choice.** DM-UI/DM-UX have not committed to a framework.
   DAI should either let them choose freely or scope-narrow them now.

## What this PR contains

- Seven Sub-AI signature surfaces under `/dm/.subai/`
- Four `AWAITING.md` placeholders (one per code-bearing folder)
- This README
- **Zero** authored DM logic, UI, UX, realism, market, review, or
  automation code

## Status

DM-Full v1 — **WIP / pre-dispatch**. The rooms are built. The minds have
not yet entered.
