from __future__ import annotations
import uuid
from typing import Annotated
from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter, Depends, status
from app.dependencies import get_tag_service, get_current_user
from app.services.tag_service import TagService
from app.models.user import User

router = APIRouter(tags=["tags"])

class TagCreate(BaseModel):
    name: str
    color: str | None = None

class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = None

class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    color: str | None = None

@router.get("/", response_model=list[TagResponse])
async def list_tags(
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[TagResponse]:
    tags = await tag_service.list_tags(current_user.id)
    return [TagResponse.model_validate(t) for t in tags]

@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TagResponse:
    tag = await tag_service.create_tag(
        user_id=current_user.id,
        name=data.name,
        color=data.color
    )
    return TagResponse.model_validate(tag)

@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: uuid.UUID,
    data: TagUpdate,
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TagResponse:
    tag = await tag_service.update_tag(
        user_id=current_user.id,
        tag_id=tag_id,
        name=data.name,
        color=data.color
    )
    return TagResponse.model_validate(tag)

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    await tag_service.delete_tag(current_user.id, tag_id)
