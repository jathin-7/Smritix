from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

class GraphNodeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    snippet: str
    memory_type: str
    tags: list[str] = []
    connection_count: int = 0
    created_at: datetime

class GraphEdgeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: uuid.UUID
    target: uuid.UUID
    relation_type: str
    confidence: float = 1.0
    created_by: str = "user"
    metadata: dict[str, Any] | None = None
    created_at: datetime

class GraphResponse(BaseModel):
    nodes: list[GraphNodeItem]
    edges: list[GraphEdgeItem]
    total_nodes: int
    total_edges: int

class CreateEdgeRequest(BaseModel):
    source_memory_id: uuid.UUID
    target_memory_id: uuid.UUID
    relation_type: str = Field(default="related_to", description="similar_to, references, related_to, part_of")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] | None = None

class ClusterItem(BaseModel):
    id: str
    name: str
    node_ids: list[uuid.UUID]
    size: int
    tags: list[str] = []
    description: str | None = None

class ClustersResponse(BaseModel):
    clusters: list[ClusterItem]
    total_clusters: int

class MemoryConnectionsResponse(BaseModel):
    memory_id: uuid.UUID
    nodes: list[GraphNodeItem]
    edges: list[GraphEdgeItem]
    total_connections: int
