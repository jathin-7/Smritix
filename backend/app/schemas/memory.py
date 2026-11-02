from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict

class CreateMemoryRequest(BaseModel):
    title: str | None = None
    content: str
    memory_type: str = "note"
    source_type: str = "manual"
    source_uri: str | None = None
    tags: list[str] | None = None
    project_ids: list[uuid.UUID] | None = None

class UpdateMemoryRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    summary: str | None = None
    memory_type: str | None = None
    tags: list[str] | None = None

class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None = None
    content: str
    summary: str | None = None
    memory_type: str
    source_type: str
    tags: list[str] = []
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime

class MemoryDetailResponse(MemoryResponse):
    chunks: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    connections_count: int = 0

class MemoryListResponse(BaseModel):
    items: list[MemoryResponse]
    total: int
    limit: int
    offset: int
