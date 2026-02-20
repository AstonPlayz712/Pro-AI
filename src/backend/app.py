"""FastAPI application factory and configuration"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routes import chat_routes


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title="Private AI Assistant",
        description="A modular AI assistant with multi-model support",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(chat_routes.router)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    # Mount static files for UI
    ui_path = Path(__file__).parent.parent.parent / "ui"
    if ui_path.exists():
        app.mount("/ui", StaticFiles(directory=str(ui_path)), name="ui")

    # Root endpoint - serve UI
    @app.get("/")
    async def root():
        ui_index = Path(__file__).parent.parent.parent / "ui" / "index.html"
        if ui_index.exists():
            return FileResponse(str(ui_index))
        return {
            "message": "Welcome to Private AI Assistant",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "chat": "/api/chat",
                "models": "/api/models",
                "ui": "/ui/index.html",
            },
        }

    return app
