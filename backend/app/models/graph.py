from __future__ import annotations
import uuid
from typing import Any
from sqlalchemy import String, Float, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class KnowledgeEdge(BaseModel):
    __tablename__ = "knowledge_edges"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    source_memory_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("memories.id"))
    target_memory_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("memories.id"))
    relation_type: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_by: Mapped[str] = mapped_column(String) # 'user', 'ai', 'system'
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    __table_args__ = (
        UniqueConstraint("source_memory_id", "target_memory_id", "relation_type", name="uix_knowledge_edge"),
    )
