from __future__ import annotations
import uuid
from typing import Sequence
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, ConversationMessage
from app.repositories.base import BaseRepository

class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: AsyncSession):
        super().__init__(Conversation, session)

    async def get_user_conversations(self, user_id: uuid.UUID) -> Sequence[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.updated_at.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().unique().all()

    async def get_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Conversation | None:
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_conversation_messages(self, conversation_id: uuid.UUID) -> list[ConversationMessage]:
        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def create_conversation(self, user_id: uuid.UUID, title: str | None = None) -> Conversation:
        conv = Conversation(
            user_id=user_id,
            title=title or "New Conversation"
        )
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        source_memories: list[str] | None = None
    ) -> ConversationMessage:
        msg = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            source_memories=source_memories or []
        )
        self.session.add(msg)
        
        await self.session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=func.now())
        )
            
        await self.session.flush()
        return msg

    async def delete_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = delete(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0
