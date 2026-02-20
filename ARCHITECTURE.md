# Architecture & Data Flow Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Client Application                           │
│         (Browser, Python, cURL, Mobile, etc.)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    FastAPI Server                               │
│                  (localhost:8000)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐        ┌──────────────────┐             │
│  │  Middleware      │        │  Routes          │             │
│  │  - CORS          │        │  - /health       │             │
│  │  - Logging       │        │  - /api/chat     │             │
│  │  - Error Handle  │        │  - /api/models   │             │
│  │                  │        │  - /api/memory   │             │
│  └──────────────────┘        └────────┬─────────┘             │
│                                       │                        │
│                          ┌────────────▼─────────┐             │
│                          │   chat_routes.py     │             │
│                          │  (Request Handler)   │             │
│                          └────────────┬─────────┘             │
│                                       │                        │
└───────────────────────────────────────┼────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
        ┌───────────▼──────┐  ┌────────▼──────┐  ┌─────────▼────────┐
        │  Config Module   │  │ ModelRouter   │  │ Memory Module    │
        │  (Settings)      │  │               │  │ (JSONMemory)     │
        │                  │  │  - OpenAI     │  │                  │
        │  Load from .env  │  │  - Anthropic  │  │ Stores in JSON   │
        │  Create cache    │  │  - Google     │  │ File             │
        └──────────────────┘  │  - Ollama     │  │                  │
                              │  (API routing)│  │ data/memory.json │
                              └────────┬──────┘  └──────────────────┘
                                       │
                 ┌─────────────────────┼──────────────────┐
                 │                     │                  │
        ┌────────▼────────┐  ┌─────────▼──────┐  ┌───────▼───────┐
        │   OpenAI API    │  │  Anthropic API │  │  Google API   │
        │  (gpt-4, etc.)  │  │ (Claude)       │  │  (Gemini)     │
        └─────────────────┘  └────────────────┘  └───────────────┘

        ┌──────────────────────────────────────┐
        │      Ollama Server (Local)           │
        │    (localhost:11434)                 │
        │   (no API key needed)                │
        └──────────────────────────────────────┘

        ┌──────────────────────────────────────┐
        │      Tools Module (Stubs)            │
        │  - WebSearch                         │
        │  - FileTools                         │
        │  - BrowserAutomation                 │
        └──────────────────────────────────────┘
```

## Request Flow Diagram

```
User Request (Chat)
        │
        ▼
┌─────────────────────────────┐
│  POST /api/chat             │
│  {                          │
│    "messages": [...],       │
│    "model": "openai",       │
│    "temperature": 0.7       │
│  }                          │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  Request Validation         │
│  (Pydantic)                 │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  Load Settings              │
│  (get_settings())           │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  Save to Memory             │
│  (Store user message)       │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  Route to Model             │
│  (ModelRouter.chat())       │
└─────────────────────────────┘
        │
        ├─────────────────────────┐
        │                         │
        ▼                         ▼
    ┌──────────┐            ┌──────────────┐
    │ OpenAI   │            │  Anthropic   │
    │  Call    │            │   Call       │
    │  API     │            │   API        │
    └──────────┘            └──────────────┘
        │                         │
        └────────────┬────────────┘
                     │
                     ▼
            ┌─────────────────────┐
            │ Normalize Response  │
            │ (Consistent format) │
            └─────────────────────┘
                     │
                     ▼
            ┌─────────────────────┐
            │ Save to Memory      │
            │ (Store response)    │
            └─────────────────────┘
                     │
                     ▼
            ┌─────────────────────┐
            │ Return Response     │
            │ {                   │
            │   "model": "...",   │
            │   "content": "...", │
            │   "usage": {...}    │
            │ }                   │
            └─────────────────────┘
```

## Module Dependencies Graph

```
main.py
  │
  └─ src.backend.create_app()
      │
      ├─ src.backend.app.create_app()
      │  │
      │  ├─ fastapi.FastAPI()
      │  ├─ CORSMiddleware
      │  └─ src.backend.routes.chat_routes
      │     │
      │     ├─ src.config.get_settings()
      │     │  └─ src.config.settings.Settings
      │     │     └─ dotenv.load_dotenv()
      │     │
      │     ├─ src.models.ModelRouter()
      │     │  ├─ openai API
      │     │  ├─ anthropic API
      │     │  ├─ google.generativeai
      │     │  └─ httpx (for Ollama)
      │     │
      │     └─ src.memory.JSONMemory()
      │        └─ json, os (file operations)
      │
      └─ uvicorn.run()
```

## Configuration Hierarchy

```
┌──────────────────────────────────┐
│      System Environment          │
│      (OS variables)              │
└────────────────┬─────────────────┘
                 │
                 ▼
┌──────────────────────────────────┐
│   .env File (local override)     │
│   (python-dotenv loads)          │
└────────────────┬─────────────────┘
                 │
                 ▼
┌──────────────────────────────────┐
│   Settings Class                 │
│   (Loads & caches config)        │
└────────────────┬─────────────────┘
                 │
                 ▼
┌──────────────────────────────────┐
│   Application Uses Settings      │
│   (get_settings() singleton)     │
└──────────────────────────────────┘
```

## Memory Flow

```
User Message
     │
     ▼
┌──────────────────────────────┐
│  Add Entry to Memory         │
│  (role="user", content=...)  │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Read memory.json            │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Append to conversations[]   │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Trim old entries            │
│  (keep last MAX_ENTRIES)     │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Write back to memory.json   │
└──────────────────────────────┘


Later - Get Memory
     │
     ▼
┌──────────────────────────────┐
│  Read memory.json            │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Parse JSON entries          │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Get recent N entries        │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Return to user              │
└──────────────────────────────┘
```

## Model Routing Logic

```
Request arrives with model="openai"
     │
     ▼
┌─────────────────────────────────┐
│ ModelRouter.chat()              │
│ Check model parameter           │
└─────────┬───────────────────────┘
          │
          ├─ "openai" ──────────┐
          │                     │
          ├─ "anthropic" ────┐  │
          │                  │  │
          ├─ "google" ───┐   │  │
          │              │   │  │
          └─ "ollama" ─┐ │   │  │
                       │ │   │  │
                       ▼ ▼   ▼  ▼
                  ┌──────────────────────┐
                  │ _chat_<provider>()   │
                  │ (Async API call)     │
                  └──────┬───────────────┘
                         │
                         ▼
                  ┌──────────────────────┐
                  │ Parse Response       │
                  │ Format Consistently  │
                  └──────┬───────────────┘
                         │
                         ▼
                  ┌──────────────────────┐
                  │ Return Normalized    │
                  │ {model, content,...} │
                  └──────────────────────┘
```

## File Organization by Function

```
Configuration Functions:
├─ src/config/settings.py        → Settings management
├─ .env                          → Local configuration
└─ .env.example                  → Config template

API Functions:
├─ main.py                       → Start server
├─ src/backend/app.py            → Create FastAPI app
├─ src/backend/routes/           → API endpoints
└─ uvicorn                       → ASGI server

Model Functions:
└─ src/models/router.py          → LLM routing

Memory Functions:
└─ src/memory/json_memory.py     → Store conversations

Tool Functions:
├─ src/tools/web_search.py       → Search stub
├─ src/tools/file_tools.py       → File operations
└─ src/tools/browser.py          → Browser automation

Utilities:
├─ verify_setup.py               → Check setup
├─ test_api.py                   → Test endpoints
└─ setup.sh                      → Auto setup

Documentation:
├─ README.md                     → Main docs
├─ API_USAGE_GUIDE.md            → API reference
├─ PROJECT_DOCUMENTATION.py      → Technical docs
├─ PROJECT_STRUCTURE.py          → Structure guide
├─ QUICK_REFERENCE.md            → Quick ref
└─ MANIFEST.md                   → File listing
```

## Server Startup Sequence

```
1. python main.py
   │
   ▼
2. Load Settings (.env)
   │
   ▼
3. Create FastAPI app
   │
   ▼
4. Setup middleware (CORS, etc)
   │
   ▼
5. Mount routes
   │
   ▼
6. Initialize ModelRouter
   │
   ▼
7. Initialize JSONMemory
   │
   ▼
8. Start Uvicorn server
   │
   ▼
9. Listen on 0.0.0.0:8000
   │
   ▼
10. Ready for requests!
    API Docs: http://localhost:8000/docs
    Root: http://localhost:8000/
    Chat: http://localhost:8000/api/chat
```

## Error Handling Flow

```
Request arrives
     │
     ▼
┌──────────────────────────────┐
│  Try to process              │
└──────┬───────────────────────┘
       │
       ├─ Success
       │  └─ Return 200
       │     with response
       │
       └─ Error
          │
          ├─ Validation Error → 400
          ├─ Not Found → 404
          ├─ API Error → 400
          │  (with error message)
          └─ Server Error → 500
```

## Data Structures

### Chat Request
```
{
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "model": "openai",           # optional
  "temperature": 0.7,          # optional
  "max_tokens": 2000           # optional
}
```

### Chat Response
```
{
  "model": "openai",
  "content": "The response text...",
  "usage": {
    "input_tokens": 15,
    "output_tokens": 45
  },
  "error": null  # if error occurred
}
```

### Memory Entry (JSON)
```
{
  "timestamp": "2024-01-24T12:00:00.000000",
  "role": "user",
  "content": "The message...",
  "model": "openai",  # null for user messages
  "metadata": {...}
}
```

---

These diagrams show the complete architecture, data flow, and module relationships of the Private AI Assistant project.
