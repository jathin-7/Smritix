from __future__ import annotations
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any
from sqlalchemy import String, Text, DateTime, ForeignKey, ARRAY, JSON, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User

class Conversation(BaseModel):
    __tablename__ = "conversations"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[list["ConversationMessage"]] = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan", lazy="selectin")

class ConversationMessage(BaseModel):
    __tablename__ = "conversation_messages"
    
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    source_memories: Mapped[list[Any] | None] = mapped_column(ARRAY(PGUUID(as_uuid=True)).with_variant(JSON, "sqlite"), nullable=True)
    
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
