# Offline Mode & Dual Engines

This repository implements a connectivity-aware hybrid AI chat system with two engines:

- **Cloud engine**: streaming OpenAI-compatible chat completions (requires API key).
- **Local engine**: streaming via a local Ollama server (works fully offline).

## Key Concepts

### Connectivity detection
Client-side connectivity uses the Network Information API when available:
- `navigator.onLine`
- `navigator.connection.type`
- `navigator.connection.effectiveType`
- `navigator.connection.downlink`
- `navigator.connection.rtt`
- `navigator.connection.saveData`

To avoid CORS issues and to keep timeouts reliable, the UI also calls server health endpoints:
- `GET /api/health/internet` (short-timeout HEAD check)
- `GET /api/health/cloud` (tiny cloud LLM streaming probe)
- `GET /api/health/local` (checks local Ollama server availability)

Implementation:
- ui/core/connectivity.ts
- ui/app/api/health/*

### Slow-connection logic
The UI marks the connection as **slow** when any of the following is true:
- `effectiveType` is `slow-2g` or `2g`
- `downlink` is very low (heuristic)
- `rtt` is very high (heuristic)
- `saveData` is enabled

### Dual engines
- Cloud engine: ui/engines/cloudEngine.ts
- Local engine: ui/engines/localEngine.ts

Both implement the shared interface:
- ui/core/chatEngine.ts
- ui/core/chatTypes.ts

### Engine selection (Auto / Force Cloud / Force Local)
Engine mode is stored locally in IndexedDB.

- **Auto**: if `realInternet === true && isSlow === false && cloudHealthy === true` → cloud.
  Otherwise → local.
- **Force Cloud**: always attempt cloud.
- **Force Local**: always use local.

Implementation:
- ui/core/engineSelector.ts

### Hybrid mode
When Auto mode selects **local due to slowness/instability**, the system stays local for LLM calls.
It can still perform **small online requests** (health checks, metadata/settings sync), but does not allow cloud LLM calls.

### Backend chat route (streaming)
`POST /api/chat`
- Accepts `{ messages, mode }`
- Attaches a **client connectivity snapshot** in Auto mode so server selection matches the real observed network quality.
- Streams plain text chunks back to the client.
- Returns `x-engine-id` response header (`cloud` or `local`).

Implementation:
- ui/app/api/chat/route.ts
- ui/engines/backendEngine.ts

### Settings panel
- Engine mode selector
- Cloud model selector
- Local model selector
- Connectivity diagnostics

Route:
- `/settings`

Implementation:
- ui/components/SettingsPanel.tsx

### Diagnostics panel
Local engine test harness:
- `/diagnostics`
- `GET /api/diagnostics/local`

Measures:
- response time
- streaming speed (chars/sec)

### Offline persistence (unlimited chats)
Chats are stored in IndexedDB via `idb`:
- conversations
- messages
- settings
- telemetry (local only)
- sync queue

Implementation:
- ui/storage/db.ts

### Offline sync queue
A lightweight queue stores pending sync items and retries when the connection becomes stable.

Implementation:
- ui/sync/offlineSync.ts
- ui/app/api/sync/route.ts (placeholder)

### Local-only telemetry
Connectivity and engine usage are recorded locally (IndexedDB) for diagnostics.

Implementation:
- ui/telemetry/telemetry.ts
- ui/hooks/useConnectivity.ts

## How to run

### Start the UI
```bash
cd ui
npm install
npm run dev
```

### Run local model (Ollama)
Install Ollama and pull a small model:
```bash
ollama pull phi3
```
Then start Ollama (default port `11434`).

### Cloud engine
Set env vars for an OpenAI-compatible provider:
- `CLOUD_API_KEY` (or `OPENAI_API_KEY`)
- optional `CLOUD_BASE_URL` (or `OPENAI_BASE_URL`)
- optional `CLOUD_MODEL`

## Testing scenarios

- **Offline**: disable network → banner shows offline, chat uses local engine.
- **Slow connection**: enable `Save-Data` or throttle network → banner shows slow, chat uses local.
- **Stable online**: banner shows full capabilities, chat uses cloud.
- **Force Local / Force Cloud**: set in Settings.
