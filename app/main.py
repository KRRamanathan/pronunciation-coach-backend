"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.session import Base, engine
from app.routes import analyze, consent, privacy
from app.services import phoneme_id, whisper_stt
from app.services.retention import retention_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_models_loaded = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _models_loaded
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Load ML models on startup
    logger.info("Loading speech models (this may take a minute on cold start)...")
    whisper_stt.load_model()
    phoneme_id.load_model()
    _models_loaded = True
    logger.info("All models loaded and ready.")

    # Start retention background task
    retention_task = asyncio.create_task(retention_loop())

    yield

    retention_task.cancel()
    try:
        await retention_task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Pronunciation Coach API",
        description="Open-source English pronunciation scoring — zero API keys required.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(consent.router, prefix="/api", tags=["consent"])
    app.include_router(analyze.router, prefix="/api", tags=["analyze"])
    app.include_router(privacy.router, prefix="/api", tags=["privacy"])

    @app.get("/api/health")
    async def health():
        return {
            "status": "ok" if _models_loaded else "loading",
            "models_loaded": _models_loaded,
        }

    return app


app = create_app()
