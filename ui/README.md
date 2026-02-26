# Pro-AI UI

Connectivity-aware hybrid workspace UI with cloud/local engines, offline sync, diagnostics, and a new unified multi-project platform layer.

## Platform Extension Layer

The current architecture is preserved and extended with project-scoped abstractions:

- Project contracts and registry: `core/platformProjects.ts`
- Project action routing: `core/platformRouter.ts`
- Active project context: `context/ProjectContext.tsx` + `hooks/useProjectManager.ts`
- Unified task endpoint: `app/api/platform/route.ts`
- Project discovery endpoint: `app/api/projects/route.ts`

Supported project IDs:

- `chatbot`
- `tube-map`
- `tfl-live-updates`
- `routing`
- `offline-tools`
- `diagnostics`
- `sync`

## Existing Hybrid Runtime (unchanged, extended)

- Connectivity checks + cloud health: `core/connectivity.ts`
- Engine selection policy: `core/engineSelector.ts`
- Cloud/local inference engines: `engines/cloudEngine.ts`, `engines/localEngine.ts`
- Backend route-based chat engine: `engines/backendEngine.ts`
- Chat route with project-scoped system context: `app/api/chat/route.ts`
- Offline queue + sync: `storage/db.ts`, `sync/offlineSync.ts`, `app/api/sync/route.ts`

## Run

```bash
npm install
npm run dev
```

## Validate

```bash
npm run lint
npm test
npm run build
```
