from __future__ import annotations
import uuid
from typing import Annotated
from fastapi import Depends, Header, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.db.session import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedError
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.memory_service import MemoryService
from app.services.tag_service import TagService
from app.services.ingest_service import IngestService
from app.services.search_service import SearchService
from app.services.rag_service import RAGService
from app.services.graph_service import GraphService
from app.services.dashboard_service import DashboardService

settings = get_settings()

async def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    return AuthService(db)

async def get_memory_service(db: Annotated[AsyncSession, Depends(get_db)]) -> MemoryService:
    return MemoryService(db)

async def get_tag_service(db: Annotated[AsyncSession, Depends(get_db)]) -> TagService:
    return TagService(db)

async def get_ingest_service(db: Annotated[AsyncSession, Depends(get_db)]) -> IngestService:
    return IngestService(db)

async def get_search_service(db: Annotated[AsyncSession, Depends(get_db)]) -> SearchService:
    return SearchService(db)

async def get_rag_service(db: Annotated[AsyncSession, Depends(get_db)]) -> RAGService:
    return RAGService(db)

async def get_graph_service(db: Annotated[AsyncSession, Depends(get_db)]) -> GraphService:
    return GraphService(db)

async def get_dashboard_service(db: Annotated[AsyncSession, Depends(get_db)]) -> DashboardService:
    return DashboardService(db)

async def get_current_user(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    token: str | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif access_token:
        token = access_token

    if token:
        try:
            payload = decode_token(token)
            user_id_str = payload.get("sub")
            if user_id_str:
                user_id = uuid.UUID(str(user_id_str))
                return await auth_service.get_user_by_id(user_id)
        except Exception:
            pass  # Fallback to single user mode if enabled, else fail

    if settings.SINGLE_USER_MODE:
        return await auth_service.get_or_create_default_user()

    raise UnauthorizedError("Authentication credentials were not provided or are invalid")
