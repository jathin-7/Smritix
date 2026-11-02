from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class IngestionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_type: str
    source_uri: str
    status: str
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

class IngestionJobListResponse(BaseModel):
    items: list[IngestionJobResponse]
    total: int

class IngestTextRequest(BaseModel):
    title: str | None = None
    content: str
    source_type: str = "text"
    tags: list[str] | None = None
