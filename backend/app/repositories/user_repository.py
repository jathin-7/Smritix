from __future__ import annotations
import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email.lower().strip()))
        return result.scalar_one_or_none()

    async def get_first_user(self) -> User | None:
        result = await self.session.execute(select(User).limit(1))
        return result.scalar_one_or_none()

    async def count_users(self) -> int:
        result = await self.session.execute(select(User.id))
        return len(result.scalars().all())
