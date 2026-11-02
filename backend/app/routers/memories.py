from __future__ import annotations
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from app.dependencies import get_memory_service, get_current_user, get_graph_service, get_search_service
from app.services.memory_service import MemoryService
from app.services.graph_service import GraphService
from app.services.search_service import SearchService
from app.models.user import User
from app.models.memory import Memory
from app.schemas.memory import (
    CreateMemoryRequest,
    UpdateMemoryRequest,
    MemoryResponse,
    MemoryDetailResponse,
    MemoryListResponse
)
from app.schemas.graph import MemoryConnectionsResponse
from app.schemas.search import SearchResultItem
from app.schemas.common import SuccessResponse

router = APIRouter(tags=["memories"])

def format_memory_response(m: Memory) -> MemoryResponse:
    tag_names = [t.name for t in m.tags] if hasattr(m, "tags") and m.tags else []
    return MemoryResponse(
        id=m.id,
        title=m.title,
        content=m.content,
        summary=m.summary,
        memory_type=m.memory_type,
        source_type=m.source_type,
        tags=tag_names,
        is_archived=m.is_archived,
        created_at=m.created_at,
        updated_at=m.updated_at
    )

def format_memory_detail(m: Memory) -> MemoryDetailResponse:
    base = format_memory_response(m)
    chunk_list = [
        {"id": str(c.id), "chunk_index": c.chunk_index, "content": c.content, "token_count": c.token_count}
        for c in (m.chunks or [])
    ]
    source_list = [
        {"id": str(s.id), "source_type": s.source_type, "source_uri": s.source_uri, "source_title": s.source_title}
        for s in (m.sources or [])
    ]
    return MemoryDetailResponse(
        **base.model_dump(),
        chunks=chunk_list,
        sources=source_list,
        connections_count=0
    )

@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    data: CreateMemoryRequest,
    memory_service: Annotated[MemoryService, Depends(get_memory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MemoryResponse:
    memory = await memory_service.create_memory(current_user.id, data)
    return format_memory_response(memory)

@router.get("/", response_model=MemoryListResponse)
async def list_memories(
    memory_service: Annotated[MemoryService, Depends(get_memory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    query: str | None = Query(None, description="Search query in title or content"),
    tag: str | None = Query(None, description="Filter by tag name"),
    memory_type: str | None = Query(None, description="Filter by memory type (note, document, etc.)"),
    is_archived: bool = Query(False, description="Whether to include archived memories"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> MemoryListResponse:
    memories, total = await memory_service.list_memories(
        user_id=current_user.id,
        memory_type=memory_type,
        tag_name=tag,
        query=query,
        is_archived=is_archived,
        limit=limit,
        offset=offset
    )
    items = [format_memory_response(m) for m in memories]
    return MemoryListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )

@router.get("/{memory_id}", response_model=MemoryDetailResponse)
async def get_memory(
    memory_id: uuid.UUID,
    memory_service: Annotated[MemoryService, Depends(get_memory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MemoryDetailResponse:
    memory = await memory_service.get_memory(memory_id, current_user.id)
    return format_memory_detail(memory)

@router.patch("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: uuid.UUID,
    data: UpdateMemoryRequest,
    memory_service: Annotated[MemoryService, Depends(get_memory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MemoryResponse:
    memory = await memory_service.update_memory(memory_id, current_user.id, data)
    return format_memory_response(memory)

@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: uuid.UUID,
    memory_service: Annotated[MemoryService, Depends(get_memory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    await memory_service.delete_memory(memory_id, current_user.id)

@router.post("/{memory_id}/archive", response_model=MemoryResponse)
async def archive_memory(
    memory_id: uuid.UUID,
    memory_service: Annotated[MemoryService, Depends(get_memory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MemoryResponse:
    memory = await memory_service.archive_memory(memory_id, current_user.id, archived=True)
    return format_memory_response(memory)

@router.post("/{memory_id}/restore", response_model=MemoryResponse)
async def restore_memory(
    memory_id: uuid.UUID,
    memory_service: Annotated[MemoryService, Depends(get_memory_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MemoryResponse:
    memory = await memory_service.archive_memory(memory_id, current_user.id, archived=False)
    return format_memory_response(memory)

@router.get("/{memory_id}/connections", response_model=SuccessResponse)
async def get_memory_connections(
    memory_id: uuid.UUID,
    graph_service: Annotated[GraphService, Depends(get_graph_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    depth: int = Query(default=1, ge=1, le=3)
) -> SuccessResponse:
    """
    Retrieve knowledge graph connections for a specific memory.
    """
    res = await graph_service.get_node_connections(
        memory_id=memory_id,
        user_id=current_user.id,
        depth=depth
    )
    return SuccessResponse(data=res)

@router.get("/{memory_id}/similar", response_model=SuccessResponse)
async def get_similar_memories(
    memory_id: uuid.UUID,
    memory_service: Annotated[MemoryService, Depends(get_memory_service)],
    search_service: Annotated[SearchService, Depends(get_search_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=5, ge=1, le=20)
) -> SuccessResponse:
    """
    Find semantically similar memories using dense vector embeddings.
    """
    memory = await memory_service.get_memory(memory_id, current_user.id)
    similar = await search_service.semantic_search(
        user_id=current_user.id,
        query=memory.content,
        limit=limit + 1
    )
    # Filter out self
    results = [s for s in similar if s.memory_id != memory_id][:limit]
    return SuccessResponse(data=results)
