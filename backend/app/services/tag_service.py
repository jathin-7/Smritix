from __future__ import annotations
import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.tag_repository import TagRepository
from app.models.memory import Tag
from app.core.exceptions import NotFoundError, ConflictError

class TagService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tag_repo = TagRepository(session)

    async def list_tags(self, user_id: uuid.UUID) -> Sequence[Tag]:
        return await self.tag_repo.get_all_for_user(user_id)

    async def create_tag(self, user_id: uuid.UUID, name: str, color: str | None = None) -> Tag:
        tag = await self.tag_repo.get_or_create(user_id, name, color)
        await self.session.commit()
        return tag

    async def update_tag(
        self,
        user_id: uuid.UUID,
        tag_id: uuid.UUID,
        name: str | None = None,
        color: str | None = None
    ) -> Tag:
        tag = await self.tag_repo.get_by_id(tag_id)
        if not tag or tag.user_id != user_id:
            raise NotFoundError("Tag not found")
        if name is not None:
            cleaned = name.strip()
            existing = await self.tag_repo.get_by_name(user_id, cleaned)
            if existing and existing.id != tag_id:
                raise ConflictError("A tag with this name already exists")
            tag.name = cleaned
        if color is not None:
            tag.color = color.strip() if color else None
        await self.session.commit()
        return tag

    async def delete_tag(self, user_id: uuid.UUID, tag_id: uuid.UUID) -> bool:
        tag = await self.tag_repo.get_by_id(tag_id)
        if not tag or tag.user_id != user_id:
            raise NotFoundError("Tag not found")
        deleted = await self.tag_repo.delete(tag_id)
        await self.session.commit()
        return deleted
