from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    memory_type: str | None = None
    tag: str | None = None
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)

class SearchResultItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    memory_id: uuid.UUID
    title: str | None = None
    snippet: str
    memory_type: str
    score: float
    tags: list[str] = []
    chunk_index: int | None = None
    created_at: datetime

class SearchResponse(BaseModel):
    query: str
    search_type: str
    results: list[SearchResultItem]
    total: int

class SearchHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    query: str
    search_type: str
    results_count: int | None = None
    created_at: datetime

class SearchHistoryResponse(BaseModel):
    items: list[SearchHistoryItem]
    total: int
