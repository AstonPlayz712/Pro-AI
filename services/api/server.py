"""
server.py — FastAPI HTTP layer for Director-AI.

Endpoints
---------
GET  /health          — liveness probe
GET  /config          — non-secret config summary (which backends are active)
POST /diagnose        — multipart/form-data: `text` + optional `images[]`
                        Returns: JSON DAIResponse

Static UI
---------
The `ui/director/` folder is served at /ui so the single-page frontend can
be opened at http://localhost:8000/ui/.

Run
---
    uvicorn services.api.server:app --reload --port 8000
"""

from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.config import get_config
from director.core.dai import create_dai
from director.core.schema import DAIRequest

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

CONFIG = get_config()
REPO_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = (REPO_ROOT / CONFIG.upload_dir).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

UI_DIR = REPO_ROOT / "ui" / "director"

# Single DAI instance for the process (stateless — safe to share)
DAI = create_dai()
logger.info("Director-AI ready.")

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Director-AI API",
    version="1.0.0",
    description="HTTP interface to the Pro-AI Director orchestrator.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
def config_summary() -> dict[str, Any]:
    """Report which backends are active, without leaking secrets."""
    return {
        "vision_backend": type(DAI.vision_tool).__name__,
        "web_backend":    type(DAI.web_tool).__name__,
        "keys": {
            "anthropic": bool(CONFIG.anthropic_api_key),
            "openai":    bool(CONFIG.openai_api_key),
            "google":    bool(CONFIG.google_api_key),
            "google_cse":bool(CONFIG.google_cse_id),
            "brave":     bool(CONFIG.brave_api_key),
        },
    }


@app.post("/diagnose")
async def diagnose(
    text:    str              = Form(""),
    device_model: str         = Form(""),
    images:  list[UploadFile] = File(default_factory=list),
) -> JSONResponse:
    """
    Main diagnostic endpoint.

    Accepts:
      text          — problem description
      device_model  — optional device identifier (e.g. "MacBook Pro 2010")
      images[]      — zero or more image uploads
    """
    if not text and not images:
        raise HTTPException(
            status_code=400,
            detail="Provide at least `text` or one image in `images`.",
        )

    # Persist uploads to disk so the vision backend can read them
    saved_paths: list[str] = []
    for upload in images:
        if not upload.filename:
            continue
        dest = _persist_upload(upload)
        saved_paths.append(str(dest))

    request = DAIRequest(
        raw_text=text,
        image_paths=saved_paths,
        context={"device_model": device_model} if device_model else {},
    )

    try:
        response = DAI.handle(request)
        return JSONResponse(response.to_dict())
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Diagnose failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _persist_upload(upload: UploadFile) -> Path:
    """Stream an upload to disk, enforcing size limits. Returns saved path."""
    suffix = Path(upload.filename or "").suffix.lower() or ".bin"
    dest = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"

    size = 0
    with open(dest, "wb") as fh:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > CONFIG.max_upload_bytes:
                fh.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"Upload too large (> {CONFIG.max_upload_bytes} bytes)",
                )
            fh.write(chunk)
    logger.info("Saved upload: %s (%d bytes)", dest.name, size)
    return dest
