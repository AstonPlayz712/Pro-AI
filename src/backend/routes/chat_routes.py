"""Chat API routes"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from src.config import get_settings
from src.models import ModelRouter
from src.memory import JSONMemory

router = APIRouter(prefix="/api", tags=["chat"])

# Request/Response models
class Message(BaseModel):
    """Message model for API"""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat request model"""
    messages: List[Message]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000


class ChatResponse(BaseModel):
    """Chat response model"""
    model: str
    content: str
    usage: Optional[dict] = None
    error: Optional[str] = None


# Initialize router and memory
settings = get_settings()
model_config = {
    "default_model": settings.default_model,
    "openai": settings.get_model_config("openai"),
    "anthropic": settings.get_model_config("anthropic"),
    "google": settings.get_model_config("google"),
    "ollama": settings.get_model_config("ollama"),
}
router_instance = ModelRouter(model_config)
memory = JSONMemory(settings.memory_file, settings.max_memory_entries)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a chat message to the AI assistant.

    Args:
        request: ChatRequest with messages and optional model specification

    Returns:
        ChatResponse with model output
    """
    try:
        # Convert request messages to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Store user message in memory
        if messages:
            last_msg = messages[-1]
            if last_msg["role"] == "user":
                memory.add_entry(
                    role="user",
                    content=last_msg["content"],
                    metadata={"model_requested": request.model},
                )

        # Get response from router
        response = await router_instance.chat(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Check for errors
        if "error" in response:
            raise HTTPException(status_code=400, detail=response["error"])

        # Store assistant response in memory
        memory.add_entry(
            role="assistant",
            content=response["content"],
            model=request.model or settings.default_model,
            metadata=response.get("usage"),
        )

        return ChatResponse(
            model=response["model"],
            content=response["content"],
            usage=response.get("usage"),
        )

    except HTTPException:
        raise
    except Exception as e:
        return ChatResponse(
            model=request.model or settings.default_model,
            content="",
            error=f"Error processing request: {str(e)}",
        )


@router.get("/models")
async def get_available_models():
    """Get list of available models"""
    available_models = router_instance.get_available_models()
    return {
        "available_models": available_models,
        "default_model": settings.default_model,
    }


@router.get("/memory")
async def get_memory(limit: int = 10):
    """Get recent conversation history"""
    entries = memory.get_recent(limit)
    return {
        "entries": [
            {
                "timestamp": e.timestamp,
                "role": e.role,
                "content": e.content,
                "model": e.model,
            }
            for e in entries
        ]
    }


@router.delete("/memory")
async def clear_memory():
    """Clear all conversation history"""
    memory.clear()
    return {"message": "Memory cleared"}
