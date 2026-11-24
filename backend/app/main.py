import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import health, stream, sessions, metrics
from .core.config import settings
from .core.logging import configure_logging


DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def allowed_cors_origins() -> list[str]:
    """Allow explicit web origins; do not permit wildcard credential policies."""
    raw = os.environ.get("SONICAID_ALLOWED_ORIGINS", DEFAULT_CORS_ORIGINS)
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if "*" in origins:
        raise ValueError("Set explicit SONICAID_ALLOWED_ORIGINS rather than '*'")
    return origins


def create_app() -> FastAPI:
    configure_logging(settings.app.log_level)

    app = FastAPI(
        title="SonicAid Next-Gen",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_cors_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(stream.router)
    app.include_router(sessions.router)
    app.include_router(metrics.router)

    return app


app = create_app()
