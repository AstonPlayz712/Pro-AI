# Pro-AI Control — AutoLink + DAI UX

All-in-one UX for the AutoLink + DAI stack. One codebase, two shipping surfaces:

- **Website** — SvelteKit SPA
- **Desktop app** — Tauri native window wrapping the same SvelteKit build

Both talk to the same FastAPI backend, which calls `dai.interface.run_intelligence_task(...)` without modifying AutoLink / DAI core logic.

## Layout

```
api/                    FastAPI backend
  main.py               app + CORS + uvicorn entrypoint
  routers/
    autolink.py         POST /autolink/run, GET /autolink/ping
    dai.py              POST /dai/run, GET /dai/system-map, GET /dai/evolution-log

webui/                  SvelteKit SPA (website + source for Tauri)
  src/routes/           +layout, autolink, dai, cities2
  src/lib/components/   TaskForm, RouteView, ContextView, ResultView
  src/lib/api.ts        typed fetch wrapper
  src/lib/theme.ts      dark/light toggle store

desktop/                Tauri wrapper
  src-tauri/            Cargo + tauri.conf.json
```

## Run the backend

```bash
pip install -r requirements.txt
python -m api.main          # http://127.0.0.1:8000
```

Health check:

```bash
curl http://127.0.0.1:8000/autolink/ping
```

## Run the website (SvelteKit)

```bash
cd webui
npm install
npm run dev                 # http://localhost:5173
```

Vite proxies `/autolink` and `/dai` to the FastAPI server on port 8000.

## Run the desktop app (Tauri)

```bash
cd desktop
npm install
npm run dev                 # launches SvelteKit + a native window
```

For a native bundle:

```bash
npm run build
```

Tauri's `beforeBuildCommand` builds `webui` to a static site (`webui/build`) and packages it into the app.

## How the flow works

```
UI (SvelteKit / Tauri)
        │  POST /autolink/run
        ▼
FastAPI (api/main.py)
        │  calls
        ▼
dai.interface.run_intelligence_task(intent, payload, user_id, ...)
        │  constructs AutoTask, hands to
        ▼
AutoLink (AutoLIP)
        ├─ AutoLM  (memory)
        ├─ AutoLCE (context)
        ├─ AutoLD  (routing → AutoOD or AutoClink)
        └─ AutoOD / AutoClink (execution stubs)
        │
        ▼
Structured response returned back up the stack to the UI:
{ task_id, intent, route, context, result }
```

## Example: `POST /autolink/run`

Request body:

```json
{
  "intent": "summarize_doc",
  "payload": { "doc": "hello world" },
  "user_id": "u1",
  "session_id": "s1",
  "sensitivity": "normal",
  "complexity": "high",
  "latency_budget_ms": 2000
}
```

Response shape:

```json
{
  "task_id": "37b6bbbd-fa8e-442a-bf18-1edd11af01f6",
  "intent": "summarize_doc",
  "route": {
    "target": "AutoClink",
    "reason": "complexity=high → cloud execution",
    "confidence": 1.0
  },
  "context": {
    "memory_size": 0,
    "system_state": { "session_id": "s1", "user_id": "u1", "online": true },
    "notes": ["context built for intent='summarize_doc'"]
  },
  "result": {
    "engine": "AutoClink",
    "task_id": "37b6bbbd-fa8e-442a-bf18-1edd11af01f6",
    "intent": "summarize_doc",
    "payload": { "doc": "hello world" },
    "context_notes": ["context built for intent='summarize_doc'"]
  }
}
```

## Guarantees

- **Website mode works** — SvelteKit + Vite proxy → FastAPI → AutoLink.
- **Desktop mode works** — Tauri loads the SvelteKit dev server (dev) or the static build (release) and hits FastAPI over `http://127.0.0.1:8000`.
- **Core logic untouched** — `auto/` and `dai/` are imported, never modified. AutoLink / DAI behavior is identical regardless of which surface invokes it.
