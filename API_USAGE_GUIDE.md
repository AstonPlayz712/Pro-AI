# API Usage Guide

Complete guide for using the Private AI Assistant API.

## Quick Start

### 1. Start the Server

```bash
python main.py
```

Server will be available at `http://localhost:8000`

### 2. Check API Documentation

Visit: `http://localhost:8000/docs` (Swagger UI)

Or: `http://localhost:8000/redoc` (ReDoc)

### 3. Make Your First Request

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

## API Endpoints

### Health Check

**Endpoint:** `GET /health`

Check if the server is running.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

### Root Endpoint

**Endpoint:** `GET /`

Get information about the API.

```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "message": "Welcome to Private AI Assistant",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "chat": "/chat",
    "models": "/models"
  }
}
```

### Chat

**Endpoint:** `POST /api/chat`

Send a message and get a response from an AI model.

#### Request

```json
{
  "messages": [
    {
      "role": "user",
      "content": "What is the capital of France?"
    }
  ],
  "model": "openai",
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Parameters:**
- `messages` (required): Array of message objects with `role` ("user" or "assistant") and `content`
- `model` (optional): Model provider ("openai", "anthropic", "google", "ollama"). Uses DEFAULT_MODEL if not specified
- `temperature` (optional, default: 0.7): Randomness of output (0.0-2.0). Higher = more creative
- `max_tokens` (optional, default: 2000): Maximum response length

#### Response

```json
{
  "model": "openai",
  "content": "The capital of France is Paris. It is located in the north-central part of the country...",
  "usage": {
    "input_tokens": 15,
    "output_tokens": 45
  }
}
```

**Response Fields:**
- `model`: Which model was used
- `content`: The AI's response
- `usage`: Token usage information (varies by model)

#### Examples

**Simple Question:**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is 2+2?"}
    ]
  }'
```

**With Conversation History:**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is Python?"},
      {"role": "assistant", "content": "Python is a programming language known for its simplicity and readability."},
      {"role": "user", "content": "What can I use it for?"}
    ],
    "model": "openai",
    "temperature": 0.5,
    "max_tokens": 300
  }'
```

**With Specific Model:**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Tell me a short story"}
    ],
    "model": "anthropic",
    "temperature": 0.9,
    "max_tokens": 1000
  }'
```

**Using Local Model (Ollama):**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Explain machine learning"}
    ],
    "model": "ollama",
    "temperature": 0.7
  }'
```

### Get Available Models

**Endpoint:** `GET /api/models`

Get list of configured and available models.

```bash
curl http://localhost:8000/api/models
```

**Response:**
```json
{
  "available_models": ["openai", "anthropic", "ollama"],
  "default_model": "openai"
}
```

### Get Conversation Memory

**Endpoint:** `GET /api/memory`

Retrieve conversation history.

```bash
curl http://localhost:8000/api/memory?limit=5
```

**Parameters:**
- `limit` (optional, default: 10): Number of recent entries to retrieve

**Response:**
```json
{
  "entries": [
    {
      "timestamp": "2024-01-24T12:00:00.000000",
      "role": "user",
      "content": "What is Python?",
      "model": null
    },
    {
      "timestamp": "2024-01-24T12:00:01.000000",
      "role": "assistant",
      "content": "Python is a programming language...",
      "model": "openai"
    }
  ]
}
```

### Clear Memory

**Endpoint:** `DELETE /api/memory`

Clear all conversation history.

```bash
curl -X DELETE http://localhost:8000/api/memory
```

**Response:**
```json
{
  "message": "Memory cleared"
}
```

## Using Different Models

### OpenAI

**Requirements:**
- `OPENAI_API_KEY` in `.env`
- API key from https://platform.openai.com/api-keys

**Available Models:**
- `gpt-4` (most capable)
- `gpt-4-turbo-preview`
- `gpt-3.5-turbo` (fastest, cheapest)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "model": "openai"
  }'
```

### Anthropic

**Requirements:**
- `ANTHROPIC_API_KEY` in `.env`
- API key from https://console.anthropic.com

**Available Models:**
- `claude-3-opus-20240229` (most capable)
- `claude-3-sonnet-20240229` (balanced)
- `claude-3-haiku-20240307` (fastest)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "model": "anthropic"
  }'
```

### Google Gemini

**Requirements:**
- `GOOGLE_API_KEY` in `.env`
- API key from https://ai.google.dev

**Available Models:**
- `gemini-1.5-pro` (most capable)
- `gemini-pro` (faster)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "model": "google"
  }'
```

### Ollama (Local)

**Requirements:**
- Ollama installed from https://ollama.ai
- Server running: `ollama serve`
- Model downloaded: `ollama pull llama2`

**No API key needed - runs locally!**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "model": "ollama"
  }'
```

## Common Patterns

### Building a Conversation

```python
import httpx
import json

async def chat_conversation():
    async with httpx.AsyncClient() as client:
        messages = []
        
        # User question 1
        messages.append({"role": "user", "content": "What is machine learning?"})
        response1 = await client.post(
            "http://localhost:8000/api/chat",
            json={"messages": messages}
        )
        assistant_response = response1.json()["content"]
        messages.append({"role": "assistant", "content": assistant_response})
        print(f"Assistant: {assistant_response}")
        
        # User question 2 (with context)
        messages.append({"role": "user", "content": "Give me an example"})
        response2 = await client.post(
            "http://localhost:8000/api/chat",
            json={"messages": messages}
        )
        assistant_response = response2.json()["content"]
        messages.append({"role": "assistant", "content": assistant_response})
        print(f"Assistant: {assistant_response}")

# Run it
import asyncio
asyncio.run(chat_conversation())
```

### Error Handling

```python
import httpx

async def safe_chat(message: str):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/chat",
                json={
                    "messages": [{"role": "user", "content": message}],
                    "model": "openai"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    print(f"API Error: {data['error']}")
                else:
                    print(f"Response: {data['content']}")
            else:
                print(f"HTTP Error: {response.status_code}")
                
        except httpx.TimeoutException:
            print("Request timed out (30s)")
        except Exception as e:
            print(f"Error: {e}")

import asyncio
asyncio.run(safe_chat("Hello"))
```

### Testing with Different Models

```bash
#!/bin/bash

# Test OpenAI
echo "Testing OpenAI..."
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}],"model":"openai"}'

# Test Anthropic
echo "Testing Anthropic..."
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}],"model":"anthropic"}'

# Test Ollama
echo "Testing Ollama..."
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}],"model":"ollama"}'
```

## Response Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Valid response returned |
| 400 | Bad Request | Invalid model, malformed JSON |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Server Error | Unhandled exception |

## Tips & Best Practices

1. **Temperature Settings:**
   - 0.0 = Deterministic (same response every time)
   - 0.5-0.8 = Balanced (creative but coherent)
   - 1.0+ = Very creative (more varied)

2. **Token Management:**
   - Start with smaller max_tokens and increase as needed
   - Fewer tokens = faster response
   - Monitor API costs for OpenAI/Google/Anthropic

3. **Conversation Context:**
   - Include relevant history for better responses
   - Too much history may slow down API
   - Memory is automatically saved

4. **Model Selection:**
   - OpenAI: Best general purpose
   - Anthropic: Good for reasoning
   - Google: Good for long contexts
   - Ollama: Best for privacy/speed (local)

5. **Error Handling:**
   - Always check response status codes
   - Set timeouts for long requests
   - Implement retry logic for failures

## Documentation

Full API documentation available at:
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Support

For issues:
1. Check server is running: `python main.py`
2. Verify .env configuration
3. Check API keys are valid
4. Review logs for error messages
5. Test with `/health` endpoint
