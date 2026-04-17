# Pro-AI Control — desktop

Tauri wrapper around the SvelteKit UI. The desktop app behaves identically
to the browser version and talks to the same FastAPI backend.

## Dev

```bash
npm install
npm run dev            # launches SvelteKit dev server + Tauri window
```

Make sure FastAPI is running separately:

```bash
python -m api.main
```

## Build

```bash
npm run build          # produces a distributable native bundle in src-tauri/target
```
