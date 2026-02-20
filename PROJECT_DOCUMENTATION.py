"""
Private AI Assistant - Complete Project Documentation
=====================================================

This is a production-ready Python AI assistant built with FastAPI,
supporting multiple AI models with conversation memory.

PROJECT STRUCTURE
=================

/
├── src/                          # Main source code directory
│   ├── __init__.py              # Package initialization
│   ├── config/                  # Configuration module
│   │   ├── __init__.py
│   │   └── settings.py          # Environment variable loader
│   ├── backend/                 # FastAPI application
│   │   ├── __init__.py
│   │   ├── app.py               # FastAPI app factory
│   │   └── routes/              # API routes
│   │       ├── __init__.py
│   │       └── chat_routes.py   # Chat endpoints
│   ├── models/                  # AI model router
│   │   ├── __init__.py
│   │   └── router.py            # Multi-model router
│   ├── memory/                  # Conversation memory
│   │   ├── __init__.py
│   │   └── json_memory.py       # JSON-based storage
│   └── tools/                   # Utility tools
│       ├── __init__.py
│       ├── web_search.py        # Web search stub
│       ├── file_tools.py        # File operations
│       └── browser.py           # Browser automation stub
├── main.py                       # Application entry point
├── verify_setup.py              # Setup verification script
├── test_api.py                  # API test examples
├── setup.sh                     # Quick setup script
├── requirements.txt             # Dependencies
├── .env                         # Environment variables (local)
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
└── README.md                    # User documentation

KEY MODULES
===========

1. CONFIG MODULE (src/config/)
   Purpose: Centralized environment configuration
   Files:
     - settings.py: Settings class that loads from .env
     - __init__.py: Module exports
   Usage:
     from src.config import get_settings
     settings = get_settings()
     print(settings.api_port)

2. BACKEND MODULE (src/backend/)
   Purpose: FastAPI application and routes
   Files:
     - app.py: Creates and configures FastAPI app
     - routes/chat_routes.py: /chat, /models, /memory endpoints
   Routes:
     - GET /: Home endpoint
     - GET /health: Health check
     - POST /api/chat: Main chat endpoint
     - GET /api/models: Available models
     - GET /api/memory: Conversation history
     - DELETE /api/memory: Clear history

3. MODELS MODULE (src/models/)
   Purpose: Multi-model routing and LLM calls
   Files:
     - router.py: ModelRouter class
   Features:
     - OpenAI (GPT-4, GPT-3.5-turbo, etc.)
     - Anthropic (Claude series)
     - Google (Gemini)
     - Ollama (Local models)

4. MEMORY MODULE (src/memory/)
   Purpose: Conversation history management
   Files:
     - json_memory.py: JSONMemory class
   Features:
     - JSON-based persistent storage
     - Conversation history tracking
     - Memory retrieval and context generation

5. TOOLS MODULE (src/tools/)
   Purpose: Utility functions and tool stubs
   Files:
     - web_search.py: Web search stub
     - file_tools.py: File operations
     - browser.py: Browser automation stub
   Note: These are stubs - implement actual functionality as needed

INSTALLATION & SETUP
====================

1. Clone/Navigate to project:
   cd /workspaces/Pro-AI

2. Create virtual environment:
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies:
   pip install -r requirements.txt

4. Configure environment:
   cp .env.example .env
   # Edit .env with your API keys

5. Verify setup:
   python verify_setup.py

6. Run server:
   python main.py

RUNNING THE APPLICATION
=======================

Development Mode:
  python main.py
  # Server runs at http://localhost:8000
  # Auto-reload enabled if API_DEBUG=true

Production Mode:
  uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

With Specific Settings:
  API_PORT=9000 python main.py
  API_DEBUG=true python main.py

API DOCUMENTATION
==================

Interactive Docs (when server is running):
  Swagger UI: http://localhost:8000/docs
  ReDoc: http://localhost:8000/redoc

Main Endpoints:

1. Health Check
   GET /health
   Response: {"status": "healthy"}

2. Root
   GET /
   Response: {
     "message": "Welcome to Private AI Assistant",
     "version": "1.0.0",
     "endpoints": {...}
   }

3. Chat (Main Endpoint)
   POST /api/chat
   Request: {
     "messages": [
       {"role": "user", "content": "Your message"},
       {"role": "assistant", "content": "Response"}
     ],
     "model": "openai",          # Optional, uses DEFAULT_MODEL if not specified
     "temperature": 0.7,          # 0.0-2.0, higher = more creative
     "max_tokens": 2000          # Maximum response length
   }
   Response: {
     "model": "openai",
     "content": "Response text",
     "usage": {"input_tokens": 10, "output_tokens": 20}
   }

4. Get Available Models
   GET /api/models
   Response: {
     "available_models": ["openai", "anthropic"],
     "default_model": "openai"
   }

5. Get Memory
   GET /api/memory?limit=10
   Response: {
     "entries": [
       {
         "timestamp": "2024-01-24T12:00:00",
         "role": "user",
         "content": "...",
         "model": "openai"
       }
     ]
   }

6. Clear Memory
   DELETE /api/memory
   Response: {"message": "Memory cleared"}

CONFIGURATION
=============

Environment Variables (.env):

OpenAI:
  OPENAI_API_KEY=sk-...        # Your OpenAI API key
  OPENAI_MODEL=gpt-4           # Model name

Anthropic:
  ANTHROPIC_API_KEY=sk-ant-... # Your Anthropic API key
  ANTHROPIC_MODEL=claude-3-sonnet-20240229

Google:
  GOOGLE_API_KEY=...           # Your Google API key
  GOOGLE_MODEL=gemini-1.5-pro

Ollama (Local):
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=llama2

Server:
  API_HOST=0.0.0.0             # Server host
  API_PORT=8000                # Server port
  API_DEBUG=false              # Enable debug/reload
  DEFAULT_MODEL=openai         # Default model provider

Memory:
  MEMORY_FILE=data/memory.json # Storage location
  MAX_MEMORY_ENTRIES=1000      # Max conversations to keep

DEPENDENCIES
============

Core:
  - fastapi: Web framework
  - uvicorn: ASGI server
  - python-dotenv: Environment variable loading
  - pydantic: Data validation

AI APIs:
  - openai: OpenAI API
  - anthropic: Anthropic API
  - google-generativeai: Google Gemini API
  - httpx: Async HTTP client (for Ollama)

Utilities:
  - requests: HTTP client

EXTENDING THE PROJECT
=====================

1. Add a New Model Provider
   - Edit: src/models/router.py
   - Add method: _chat_<provider>()
   - Update config loading
   - Test thoroughly

2. Add New Tools
   - Create file in: src/tools/
   - Implement tool class
   - Export in: src/tools/__init__.py
   - Document usage

3. Add New Endpoints
   - Create file in: src/backend/routes/
   - Define routes with FastAPI
   - Include in app.py via include_router()
   - Add to __init__.py exports

4. Change Memory Storage
   - Modify: src/memory/json_memory.py
   - Implement your storage backend
   - Keep same interface for compatibility

5. Add Database Integration
   - Install ORM (SQLAlchemy, etc.)
   - Extend src/memory/ module
   - Update configuration

TESTING
=======

Run test examples:
  python test_api.py

This requires:
  1. Server running: python main.py
  2. Dependencies installed: pip install -r requirements.txt
  3. Proper .env configuration

Manual Testing with curl:

Health check:
  curl http://localhost:8000/health

Chat request:
  curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{
      "messages": [{"role": "user", "content": "Hello"}],
      "model": "openai"
    }'

SECURITY CONSIDERATIONS
=======================

1. API Keys
   - Never commit .env to git (use .env.example)
   - Rotate keys regularly
   - Use environment variables in production

2. Input Validation
   - All inputs validated with Pydantic
   - Add rate limiting for production

3. CORS
   - Currently allows all origins
   - Restrict to specific domains in production

4. Authentication
   - Add API key/token authentication
   - Consider OAuth2 for user management

5. HTTPS
   - Use HTTPS in production
   - Obtain SSL certificates

TROUBLESHOOTING
===============

Issue: "ModuleNotFoundError: No module named 'src'"
Solution: Run from project root, install requirements

Issue: "API key not working"
Solution: Check .env file exists and is in project root

Issue: "Connection refused" for Ollama
Solution: Ensure Ollama server is running (ollama serve)

Issue: "Port already in use"
Solution: Change API_PORT in .env or kill process on port

Issue: Slow responses
Solution: Check max_tokens setting, use local Ollama for speed

Issue: "Memory file not found"
Solution: Directory doesn't exist, will be created automatically

PERFORMANCE OPTIMIZATION
=======================

1. Caching
   - Settings are cached with @lru_cache
   - Add response caching for repeated queries

2. Async Operations
   - All I/O operations are async
   - Use httpx for async HTTP calls

3. Connection Pooling
   - FastAPI/Uvicorn handle connection reuse
   - Configure worker count based on CPU

4. Token Management
   - Set appropriate max_tokens limits
   - Monitor API usage and costs

5. Local Model Usage
   - Use Ollama for privacy and cost savings
   - Smaller models for faster responses

DEPLOYMENT
==========

Local Machine (Development):
  python main.py
  API: http://localhost:8000

Production Server:
  gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

Docker:
  # Create Dockerfile with Python 3.11+
  # Install requirements
  # Run: python main.py

Cloud Platforms:
  - Heroku: Use Procfile with uvicorn
  - AWS Lambda: Serverless option
  - Google Cloud Run: Container-based
  - Azure: App Service

MAINTENANCE
===========

Regular Tasks:
  1. Update dependencies: pip install --upgrade -r requirements.txt
  2. Monitor API usage and costs
  3. Review conversation memory size
  4. Check logs for errors
  5. Update API keys when expired

Monitoring:
  - Set up application logging
  - Monitor response times
  - Track error rates
  - Monitor memory usage

Backup:
  - Regular backup of memory.json
  - Store API keys securely
  - Version control code (git)

SUPPORT & RESOURCES
===================

Documentation:
  - FastAPI: https://fastapi.tiangolo.com
  - Uvicorn: https://www.uvicorn.org
  - OpenAI API: https://platform.openai.com/docs
  - Anthropic: https://console.anthropic.com
  - Google Gemini: https://ai.google.dev
  - Ollama: https://ollama.ai

Debugging:
  - Enable API_DEBUG=true for detailed logs
  - Check /docs endpoint for API structure
  - Use curl or Postman for manual testing

Common Commands:
  python main.py                  # Start server
  pip install -r requirements.txt # Install deps
  python verify_setup.py          # Check setup
  python test_api.py              # Run tests
  curl http://localhost:8000/docs # Open API docs

LICENSE & ATTRIBUTION
====================

This project is provided as-is for private use.

Libraries used are open source with appropriate licenses.
Please review their respective licenses for commercial use.

CHANGELOG
=========

v1.0.0 (Initial Release)
  - FastAPI backend with /chat endpoint
  - Multi-model router (OpenAI, Anthropic, Google, Ollama)
  - JSON-based memory module
  - Configuration with python-dotenv
  - Tool stubs (web search, file ops, browser automation)
  - Complete documentation and examples

NOTES
=====

- This is a foundation for a private AI assistant
- Extend with additional tools and features as needed
- All API calls are asynchronous for performance
- Memory is JSON-based but can be replaced with database
- Tool implementations are stubs - implement as needed
- Security hardening recommended for production use

"""

if __name__ == "__main__":
    print(__doc__)
