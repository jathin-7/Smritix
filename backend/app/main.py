from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Annotated, Any
import structlog
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import engine, get_db
import app.models  # noqa: F401
from app.models.base import Base
from app.routers import (
    auth, memories, search, ask, ingest, projects, tags, graph, dashboard, settings as settings_router, files
)
from app.core.middleware import setup_middleware

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up SMRITIX API")
    if get_db not in app.dependency_overrides:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            logger.error("Failed to initialize database tables", error=str(e))
    yield
    logger.info("Shutting down SMRITIX API")

def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title="SMRITIX API",
        version="0.1.0",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    setup_middleware(app)
    
    @app.get("/api/v1/health", tags=["health"])
    async def health_check(
        db: Annotated[AsyncSession, Depends(get_db)]
    ) -> dict[str, Any]:
        db_status = "healthy"
        try:
            await db.execute(text("SELECT 1"))
        except Exception:
            db_status = "unhealthy"
            
        return {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "version": "0.1.0",
            "database": db_status,
            "architecture": "local-first",
            "privacy_mode": "zero-cloud-egress"
        }
    
    app.include_router(auth.router, prefix="/api/v1/auth")
    app.include_router(memories.router, prefix="/api/v1/memories")
    app.include_router(search.router, prefix="/api/v1/search")
    app.include_router(ask.router, prefix="/api/v1/ask")
    app.include_router(ingest.router, prefix="/api/v1/ingest")
    app.include_router(projects.router, prefix="/api/v1/projects")
    app.include_router(tags.router, prefix="/api/v1/tags")
    app.include_router(graph.router, prefix="/api/v1/graph")
    app.include_router(dashboard.router, prefix="/api/v1/dashboard")
    app.include_router(settings_router.router, prefix="/api/v1/settings")
    app.include_router(files.router, prefix="/api/v1/files")
    
    return app

app = create_app()
