# Pro-AI UI

Samsung-style hybrid assistant runtime layered on top of the existing architecture.

## Three AI Modes

- **Local mode**: always prefers local model execution.
- **Cloud mode**: uses cloud model, with automatic temporary fallback to local while offline.
- **Hybrid mode**: connectivity-aware orchestration between local and cloud engines.

Core implementation:

- `core/aiModeManager.ts`
- `context/AiModeContext.tsx`
- `hooks/useAiModeManager.ts`

## Hybrid Behavior

Hybrid mode follows this flow:

1. Start local model immediately.
2. Start cloud model only when connectivity quality is `good`.
3. If cloud finishes first, return cloud result.
4. If cloud is unavailable/slow/offline, use local result.
5. If both finish, return local output with cloud refinement block.
6. After request, runtime returns to default mode.

Implementation:

- `engines/hybridEngine.ts`
- `core/connectivityPolicy.ts`
- `core/modeSwitching.ts`

## Temporary Mode Switching

Automatic and request-scoped switching rules:

- Default `local` + large task + good connectivity => temporary `cloud`
- Default `cloud` + offline => temporary `local`
- Default `hybrid` => hybrid decision path
- End of request => `resetToDefault()`

## File Reading

Supported upload types:

- PDF
- DOCX
- TXT/Markdown text

Flow:

1. Client uploads file to `POST /api/read-file`.
2. Server extracts text and stores it for the next request.
3. Chat request sends file content to `/api/chat`.
4. Local/cloud/hybrid engines append file text to prompt context.

Implementation:

- `app/api/read-file/route.ts`
- `core/serverFileCache.ts`
- `core/filePrompt.ts`
- `components/MessageInput.tsx`

## Connectivity Rules

`core/connectivityPolicy.ts` classifies connectivity as:

- `offline`
- `slow`
- `good`
- `unstable`

Hybrid and temporary mode switching consume this classification.

## Mode Selector UI

In chat UI:

- Select default mode: Local / Cloud / Hybrid
- View current active mode
- Mode switches can occur temporarily per request and auto-reset

Primary UI files:

- `components/ChatPanel.tsx`
- `components/MessageInput.tsx`
- `components/ModeBanner.tsx`
- `components/StatusBar.tsx`

## Unified Identity

Assistant identity and mode-aware prompts are injected in `/api/chat`:

- Unified identity prompt (same personality/tone/formatting)
- Mode prompt (`local` / `cloud` / `hybrid`)
- Existing project-scoped prompt

Implementation:

- `core/systemPrompts.ts`
- `app/api/chat/route.ts`

## Existing Platform Layer

Project-aware routing remains active:

- `core/platformProjects.ts`
- `core/platformRouter.ts`
- `app/api/projects/route.ts`
- `app/api/platform/route.ts`

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
