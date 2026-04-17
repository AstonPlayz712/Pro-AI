"""FastAPI entrypoint for the Pro-AI Control UI.

Run with:
    python -m api.main
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import autolink, dai


def create_app() -> FastAPI:
    app = FastAPI(
        title="Pro-AI Control API",
        version="0.1.0",
        description="HTTP surface over AutoLink + DAI.",
    )

    # Local dev: SvelteKit (5173) and Tauri (tauri://localhost, file://).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "tauri://localhost",
            "https://tauri.localhost",
        ],
        allow_origin_regex=r"^(tauri|file)://.*$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(autolink.router)
    app.include_router(dai.router)

    @app.get("/")
    def root() -> dict:
        return {
            "service": "pro-ai-control",
            "endpoints": ["/autolink/run", "/autolink/ping", "/dai/run", "/dai/system-map", "/dai/evolution-log"],
        }

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
