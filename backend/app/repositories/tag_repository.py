from __future__ import annotations
import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.memory import Tag
from app.repositories.base import BaseRepository

class TagRepository(BaseRepository[Tag]):
    def __init__(self, session: AsyncSession):
        super().__init__(Tag, session)

    async def get_by_name(self, user_id: uuid.UUID, name: str) -> Tag | None:
        result = await self.session.execute(
            select(Tag).where(Tag.user_id == user_id, Tag.name == name.strip())
        )
        return result.scalar_one_or_none()

    async def get_all_for_user(self, user_id: uuid.UUID) -> Sequence[Tag]:
        result = await self.session.execute(
            select(Tag).where(Tag.user_id == user_id).order_by(Tag.name.asc())
        )
        return result.scalars().all()

    async def get_or_create(self, user_id: uuid.UUID, name: str, color: str | None = None) -> Tag:
        cleaned_name = name.strip()
        existing = await self.get_by_name(user_id, cleaned_name)
        if existing:
            return existing
        return await self.create(user_id=user_id, name=cleaned_name, color=color)
