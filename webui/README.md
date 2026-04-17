# Pro-AI Control — webui

SvelteKit SPA that talks to the Pro-AI FastAPI backend.

## Dev

```bash
npm install
npm run dev            # http://localhost:5173 (proxies /autolink and /dai to FastAPI on :8000)
```

## Build

```bash
npm run build          # outputs a static site to ./build (used by Tauri)
```

Set `PUBLIC_API_BASE` in `.env` when the UI is served from a different origin
than the API (e.g. Tauri shelling to a remote deployment).
