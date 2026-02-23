from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import health, stream, sessions, metrics
from .core.config import settings
from .core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging(settings.app.log_level)

    app = FastAPI(
        title="SonicAid Next-Gen",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(stream.router)
    app.include_router(sessions.router)
    app.include_router(metrics.router)

    return app


app = create_app()

