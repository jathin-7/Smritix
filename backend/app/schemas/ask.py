from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class AskRequest(BaseModel):
    query: str = Field(min_length=1, description="User question or prompt for SMRITIX")
    conversation_id: uuid.UUID | None = Field(default=None, description="Optional existing conversation ID to continue")
    limit: int = Field(default=5, ge=1, le=20, description="Max number of candidate memory sources to retrieve")

class SourceAttributionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    index: int
    memory_id: uuid.UUID
    title: str | None = None
    snippet: str
    relevance_score: float
    memory_type: str = "note"
    is_cited: bool = False
    source_category: str = "memory" # "memory" or "file"
    file_id: uuid.UUID | None = None
    file_path: str | None = None
    page_number: int | None = None
    section_heading: str | None = None

class AskResponse(BaseModel):
    conversation_id: uuid.UUID
    answer: str
    sources: list[SourceAttributionItem] = []

class ConversationMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    sources: list[SourceAttributionItem] = []
    created_at: datetime

class ConversationItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

class ConversationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[ConversationMessageResponse] = []
