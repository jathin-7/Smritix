from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, TYPE_CHECKING
from sqlalchemy import String, DateTime, JSON, Boolean, Integer, Text, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User

class FileRoot(BaseModel):
    __tablename__ = "file_roots"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    root_path: Mapped[str] = mapped_column(String, index=True)
    display_name: Mapped[str] = mapped_column(String)
    is_monitored: Mapped[bool] = mapped_column(Boolean, default=True)
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "root_path", name="uix_user_root_path"),)

    user: Mapped["User"] = relationship("User", lazy="selectin")
    files: Mapped[list["FileRecord"]] = relationship("FileRecord", back_populates="root", cascade="all, delete-orphan", lazy="selectin")


class FileRecord(BaseModel):
    __tablename__ = "file_records"

    root_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("file_roots.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    relative_path: Mapped[str] = mapped_column(String)
    absolute_path: Mapped[str] = mapped_column(String, index=True)
    file_name: Mapped[str] = mapped_column(String, index=True)
    extension: Mapped[str] = mapped_column(String, index=True)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    modified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    indexing_status: Mapped[str] = mapped_column(String, default="pending", index=True) # pending, indexing, indexed, failed, skipped
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("root_id", "relative_path", name="uix_root_relative_path"),)

    root: Mapped["FileRoot"] = relationship("FileRoot", back_populates="files", lazy="selectin")
    chunks: Mapped[list["FileChunk"]] = relationship("FileChunk", back_populates="file", cascade="all, delete-orphan", lazy="selectin")
    versions: Mapped[list["FileVersion"]] = relationship("FileVersion", back_populates="file", cascade="all, delete-orphan", lazy="selectin")


class FileVersion(BaseModel):
    __tablename__ = "file_versions"

    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("file_records.id"))
    content_hash: Mapped[str] = mapped_column(String, index=True)
    file_size: Mapped[int] = mapped_column(Integer)
    modified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="versions", lazy="selectin")


class FileChunk(BaseModel):
    __tablename__ = "file_chunks"

    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("file_records.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_heading: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding_id: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="chunks", lazy="selectin")


class FileJob(BaseModel):
    __tablename__ = "file_jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    file_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("file_records.id", ondelete="SET NULL"), nullable=True)
    job_type: Mapped[str] = mapped_column(String) # index, reindex, delete, scan
    status: Mapped[str] = mapped_column(String, default="queued") # queued, processing, completed, failed
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FileEvent(BaseModel):
    __tablename__ = "file_events"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    root_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("file_roots.id", ondelete="CASCADE"), nullable=True)
    file_path: Mapped[str] = mapped_column(String)
    event_type: Mapped[str] = mapped_column(String) # created, modified, deleted, renamed
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
