from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Sequence, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.models.memory import Memory, Tag, MemoryTag
from app.repositories.base import BaseRepository

class MemoryRepository(BaseRepository[Memory]):
    def __init__(self, session: AsyncSession):
        super().__init__(Memory, session)

    async def get_by_id_and_user(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> Memory | None:
        stmt = select(Memory).where(
            Memory.id == memory_id,
            Memory.user_id == user_id,
            Memory.is_deleted.is_(False)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_id_loaded(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> Memory | None:
        query = (
            select(Memory)
            .where(
                Memory.id == memory_id,
                Memory.user_id == user_id,
                Memory.is_deleted.is_(False)
            )
            .options(
                selectinload(Memory.tags),
                selectinload(Memory.chunks),
                selectinload(Memory.sources)
            )
        )
        result = await self.session.execute(query)
        memory = result.scalar_one_or_none()
        if memory:
            memory.accessed_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.refresh(memory, ["updated_at", "accessed_at"])
        return memory

    async def list_memories(
        self,
        user_id: uuid.UUID,
        memory_type: str | None = None,
        tag_name: str | None = None,
        query_text: str | None = None,
        is_archived: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[Sequence[Memory], int]:
        base_filters = [
            Memory.user_id == user_id,
            Memory.is_deleted.is_(False),
            Memory.is_archived.is_(is_archived)
        ]

        if memory_type:
            base_filters.append(Memory.memory_type == memory_type)

        if query_text:
            search_pattern = f"%{query_text.strip()}%"
            base_filters.append(
                or_(
                    Memory.title.ilike(search_pattern),
                    Memory.content.ilike(search_pattern),
                    Memory.summary.ilike(search_pattern)
                )
            )

        stmt = (
            select(Memory)
            .where(*base_filters)
            .options(selectinload(Memory.tags))
        )

        if tag_name:
            stmt = stmt.join(Memory.tags).where(Tag.name == tag_name.strip())

        # Count total
        count_stmt = select(func.count(func.distinct(Memory.id))).where(*base_filters)
        if tag_name:
            count_stmt = count_stmt.join(Memory.tags).where(Tag.name == tag_name.strip())
        
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar() or 0

        # Paginate
        stmt = stmt.order_by(Memory.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    async def soft_delete(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        memory = await self.get_by_id(memory_id)
        if not memory or memory.user_id != user_id:
            return False
        memory.is_deleted = True
        await self.session.flush()
        return True

    async def set_archived(self, memory_id: uuid.UUID, user_id: uuid.UUID, archived: bool) -> Memory | None:
        memory = await self.get_by_id_loaded(memory_id, user_id)
        if not memory:
            return None
        memory.is_archived = archived
        await self.session.flush()
        return memory
