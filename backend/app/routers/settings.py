from __future__ import annotations
from typing import Annotated, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.models.user import User
from app.config import get_settings
from app.ai.registry import registry
from app.schemas.common import SuccessResponse

router = APIRouter(tags=["settings"])
settings = get_settings()

class UpdateSettingsRequest(BaseModel):
    settings_: dict[str, Any]

@router.get("", response_model=SuccessResponse)
@router.get("/", response_model=SuccessResponse)
async def get_user_settings(
    current_user: Annotated[User, Depends(get_current_user)]
) -> SuccessResponse:
    return SuccessResponse(data=current_user.settings_ or {})

@router.get("/ai", response_model=SuccessResponse)
async def get_ai_settings(
    current_user: Annotated[User, Depends(get_current_user)]
) -> SuccessResponse:
    ollama_online = await registry.is_ollama_available()
    llm = await registry.get_llm_provider()
    emb = await registry.get_embedding_provider()

    return SuccessResponse(
        data={
            "ollama_available": ollama_online,
            "ollama_url": settings.OLLAMA_BASE_URL,
            "llm_provider": llm.__class__.__name__,
            "embedding_provider": emb.__class__.__name__,
            "embedding_dimensions": emb.dimensions,
            "local_only": True,
            "privacy_first": True,
            "default_model": getattr(llm, "model", "local-fallback")
        }
    )

@router.get("/privacy", response_model=SuccessResponse)
async def get_privacy_settings(
    current_user: Annotated[User, Depends(get_current_user)]
) -> SuccessResponse:
    return SuccessResponse(
        data={
            "local_first": True,
            "telemetry_enabled": False,
            "cloud_sync_enabled": False,
            "zero_cost_local_mode": True,
            "encryption_at_rest": True
        }
    )
