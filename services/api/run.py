"""
run.py — Dev entry-point for the Director-AI FastAPI service.

Usage
-----
    python -m services.api.run
    # or
    uvicorn services.api.server:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import uvicorn

from core.config import get_config


def main() -> None:
    cfg = get_config()
    uvicorn.run(
        "services.api.server:app",
        host=cfg.host,
        port=cfg.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
