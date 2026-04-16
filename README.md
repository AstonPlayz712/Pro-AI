# Private AI Assistant

A modular, production-ready Python AI assistant with multi-model support and a beautiful web UI.

## Features

- **Multi-Model Support**: OpenAI, Anthropic, Google Gemini, and local Ollama
- **FastAPI Backend**: High-performance REST API with async support
- **Web UI**: Beautiful, responsive chat interface with dark/light mode
- **Conversation Memory**: JSON-based persistent memory management
- **Modular Architecture**: Clean separation of concerns with organized folder structure
- **Tool Stubs**: Web search, file operations, and browser automation ready for extension
- **Environment Configuration**: Easy setup with python-dotenv
- **API Documentation**: Auto-generated Swagger/OpenAPI docs at `/docs`

## Project Structure

```
/src
├── backend/          # FastAPI application
├── config/           # Settings and configuration
├── models/           # Multi-model router
├── memory/           # Conversation memory management
└── tools/            # Tool implementations (web search, files, browser)
/ui                  # Web interface (HTML, CSS, JavaScript)
main.py              # Entry point
requirements.txt     # Dependencies
.env                 # Environment variables
.env.example         # Example environment file
```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Setup

1. **Clone and navigate to the project**:
```bash
cd /workspaces/Pro-AI
```

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
DEFAULT_MODEL=openai  # or anthropic, google, ollama
```

## Running the Server

### Development Mode

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### With Debug Mode

```bash
API_DEBUG=true python main.py
```

## Using the Web UI

Once the server is running, open your browser and navigate to:

**`http://localhost:8000`**

### UI Features

- **Chat Interface**: Send messages and receive responses from AI models
- **Model Selection**: Choose between OpenAI, Anthropic, Google, or Ollama
- **Temperature Control**: Adjust creativity of responses (0.0 = focused, 2.0 = creative)
- **Max Tokens**: Control response length
- **Conversation Memory**: Chat history is automatically saved in your browser
- **Clear Chat**: Start a fresh conversation
- **Info Panel**: Learn about supported models and tips

### Web UI Components

- **`ui/index.html`**: Chat interface with model selector and settings
- **`ui/script.js`**: Frontend logic, API communication, chat management
- **`ui/style.css`**: Responsive dark/light theme styling

### Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari
- Mobile browsers (iOS Safari, Chrome Mobile)

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Chat Endpoint
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "model": "openai",
    "temperature": 0.7,
    "max_tokens": 2000
  }'
```

### Get Available Models
```bash
curl http://localhost:8000/api/models
```

### Get Conversation Memory
```bash
curl http://localhost:8000/api/memory?limit=10
```

### Clear Memory
```bash
curl -X DELETE http://localhost:8000/api/memory
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration

### Supported Models

#### OpenAI
- Requires: `OPENAI_API_KEY`
- Default model: `gpt-4`
- Models: gpt-4, gpt-4-turbo, gpt-3.5-turbo, etc.

#### Anthropic
- Requires: `ANTHROPIC_API_KEY`
- Default model: `claude-3-sonnet-20240229`
- Models: Claude 3 variants

#### Google Gemini
- Requires: `GOOGLE_API_KEY`
- Default model: `gemini-1.5-pro`
- Models: gemini-1.5-pro, gemini-pro, etc.

#### Ollama (Local)
- Requires: Ollama server running at `OLLAMA_BASE_URL`
- Default model: `llama2`
- No API key required
- Models: Any model available in Ollama

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | 0.0.0.0 | Server host |
| `API_PORT` | 8000 | Server port |
| `API_DEBUG` | false | Enable debug mode |
| `DEFAULT_MODEL` | openai | Default model provider |
| `MEMORY_FILE` | data/memory.json | Memory storage location |
| `MAX_MEMORY_ENTRIES` | 1000 | Maximum conversation entries |

## Setting Up Ollama (Local Model)

1. **Install Ollama**: https://ollama.ai

2. **Pull a model**:
```bash
ollama pull llama2
```

3. **Run Ollama server**:
```bash
ollama serve
```

4. **Set in .env**:
```env
DEFAULT_MODEL=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

## Development

### Project Layout

- **Config Module** (`src/config/`):
  - `settings.py`: Environment variable loading and configuration
  - `__init__.py`: Module exports

- **Memory Module** (`src/memory/`):
  - `json_memory.py`: JSON-based conversation storage
  - `__init__.py`: Module exports

- **Tools Module** (`src/tools/`):
  - `web_search.py`: Web search tool (stub)
  - `file_tools.py`: File operations
  - `browser.py`: Browser automation (stub)
  - `__init__.py`: Module exports

- **Models Module** (`src/models/`):
  - `router.py`: Multi-model routing logic

- **Backend Module** (`src/backend/`):
  - `app.py`: FastAPI application factory
  - `routes/`: API route definitions
  - `__init__.py`: Module exports

### Extending the Project

1. **Add a new model provider**: Extend `ModelRouter` in `src/models/router.py`
2. **Add tools**: Implement in `src/tools/` modules
3. **Add endpoints**: Create new route files in `src/backend/routes/`
4. **Add database**: Modify `src/memory/` for different storage backends

## Testing

Create a `test_api.py` file:

```python
import httpx
import asyncio

async def test_chat():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "What is Python?"}
                ],
                "model": "openai",
                "temperature": 0.7,
                "max_tokens": 500
            }
        )
        print(response.json())

asyncio.run(test_chat())
```

## Troubleshooting

### "Module not found" errors
Ensure you're running from the project root and have installed dependencies:
```bash
pip install -r requirements.txt
```

### API key errors
- Verify your `.env` file is in the project root
- Check that API keys are correctly set
- Ensure `DEFAULT_MODEL` matches an available key

### Ollama connection errors
- Ensure Ollama server is running: `ollama serve`
- Check `OLLAMA_BASE_URL` in `.env`
- Default is `http://localhost:11434`

## Performance Tips

1. Use appropriate `temperature` values (0-1)
2. Set reasonable `max_tokens` limits
3. Monitor conversation memory with `MAX_MEMORY_ENTRIES`
4. Use Ollama locally to reduce API costs
5. Enable caching for frequently asked questions

## Security Considerations

- Keep API keys in `.env` (never commit to git)
- Use environment variables in production
- Validate/sanitize user inputs
- Implement rate limiting for production
- Add authentication to API endpoints
- Use HTTPS in production

## License

This project is provided as-is for private use.

## Support

For issues or questions, review the code structure and API documentation at `/docs` endpoint.
