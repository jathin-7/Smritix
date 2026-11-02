from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class TypeBreakdownItem(BaseModel):
    memory_type: str
    count: int
    percentage: float
    color: str

class ActivityDayItem(BaseModel):
    date: str
    day_name: str
    count: int

class TopTagItem(BaseModel):
    name: str
    count: int

class DashboardStatsResponse(BaseModel):
    total_memories: int
    new_this_week: int
    total_edges: int
    total_conversations: int
    total_chunks: int
    types: list[TypeBreakdownItem]
    activity: list[ActivityDayItem]
    top_tags: list[TopTagItem]

class TimelineMemoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    snippet: str
    memory_type: str
    tags: list[str] = []
    created_at: datetime

class TimelineDayGroup(BaseModel):
    date: str
    formatted_date: str
    memories: list[TimelineMemoryItem]

class TimelineResponse(BaseModel):
    groups: list[TimelineDayGroup]
    total: int

class KnowledgeGapItem(BaseModel):
    memory_id: uuid.UUID
    title: str
    memory_type: str
    reason: str

class KnowledgeGapsResponse(BaseModel):
    gaps: list[KnowledgeGapItem]
    orphaned_count: int
    untagged_count: int
    health_score: int
