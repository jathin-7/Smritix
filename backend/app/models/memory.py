from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, TYPE_CHECKING
from sqlalchemy import String, DateTime, JSON, Boolean, Integer, Text, ForeignKey, Table, Column, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User

MemoryTag = Table(
    "memory_tags",
    Base.metadata,
    Column("memory_id", ForeignKey("memories.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

class Memory(BaseModel):
    __tablename__ = "memories"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    memory_type: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String)
    source_uri: Mapped[str | None] = mapped_column(String, nullable=True)
    source_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    user: Mapped["User"] = relationship("User", back_populates="memories")
    chunks: Mapped[list["MemoryChunk"]] = relationship("MemoryChunk", back_populates="memory", cascade="all, delete-orphan")
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary=MemoryTag, back_populates="memories")
    sources: Mapped[list["MemorySource"]] = relationship("MemorySource", back_populates="memory", cascade="all, delete-orphan")

class MemoryChunk(BaseModel):
    __tablename__ = "memory_chunks"
    
    memory_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("memories.id"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding_id: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    memory: Mapped["Memory"] = relationship("Memory", back_populates="chunks")

class Tag(BaseModel):
    __tablename__ = "tags"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String)
    color: Mapped[str | None] = mapped_column(String, nullable=True)
    
    __table_args__ = (UniqueConstraint("user_id", "name", name="uix_user_tag_name"),)
    
    user: Mapped["User"] = relationship("User", back_populates="tags")
    memories: Mapped[list["Memory"]] = relationship("Memory", secondary=MemoryTag, back_populates="tags")

class MemorySource(BaseModel):
    __tablename__ = "memory_sources"
    
    memory_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("memories.id"))
    source_type: Mapped[str] = mapped_column(String)
    source_uri: Mapped[str] = mapped_column(String)
    source_title: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_content_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    memory: Mapped["Memory"] = relationship("Memory", back_populates="sources")

class IngestionJob(BaseModel):
    __tablename__ = "ingestion_jobs"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    source_type: Mapped[str] = mapped_column(String)
    source_uri: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class MemoryAccessLog(BaseModel):
    __tablename__ = "memory_access_logs"
    
    memory_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("memories.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

class SearchHistory(BaseModel):
    __tablename__ = "search_history"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    query: Mapped[str] = mapped_column(String)
    search_type: Mapped[str] = mapped_column(String, default="hybrid")
    results_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
