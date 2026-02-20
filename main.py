"""Main entry point for the AI Assistant FastAPI server"""

import uvicorn
from src.backend import create_app
from src.config import get_settings

# Create FastAPI application
app = create_app()

if __name__ == "__main__":
    settings = get_settings()

    # Run server
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level="info",
    )
