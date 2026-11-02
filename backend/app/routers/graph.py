from __future__ import annotations
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.dependencies import get_current_user, get_graph_service
from app.models.user import User
from app.services.graph_service import GraphService
from app.schemas.graph import (
    GraphResponse,
    CreateEdgeRequest,
    GraphEdgeItem,
    ClustersResponse,
    MemoryConnectionsResponse
)
from app.schemas.common import SuccessResponse

router = APIRouter(tags=["graph"])

@router.get("", response_model=SuccessResponse)
@router.get("/", response_model=SuccessResponse)
async def get_graph(
    current_user: Annotated[User, Depends(get_current_user)],
    graph_service: Annotated[GraphService, Depends(get_graph_service)],
    tag: str | None = Query(default=None, description="Filter graph by tag"),
    memory_type: str | None = Query(default=None, description="Filter graph by memory type"),
    limit: int = Query(default=150, ge=1, le=500, description="Max memories to return in graph")
) -> SuccessResponse:
    """
    Retrieve full user knowledge graph (nodes and knowledge edges).
    """
    graph_data = await graph_service.get_graph(
        user_id=current_user.id,
        tag=tag,
        memory_type=memory_type,
        limit=limit
    )
    return SuccessResponse(data=graph_data)

@router.get("/connections", response_model=SuccessResponse)
async def get_node_connections(
    memory_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    graph_service: Annotated[GraphService, Depends(get_graph_service)],
    depth: int = Query(default=1, ge=1, le=3, description="Traversal hop depth")
) -> SuccessResponse:
    """
    Traverse connections centered on a specific memory node up to N hops.
    """
    connections = await graph_service.get_node_connections(
        memory_id=memory_id,
        user_id=current_user.id,
        depth=depth
    )
    return SuccessResponse(data=connections)

@router.get("/clusters", response_model=SuccessResponse)
async def get_clusters(
    current_user: Annotated[User, Depends(get_current_user)],
    graph_service: Annotated[GraphService, Depends(get_graph_service)]
) -> SuccessResponse:
    """
    Retrieve semantic clusters and connected components in the knowledge graph.
    """
    clusters = await graph_service.get_clusters(user_id=current_user.id)
    return SuccessResponse(data=clusters)

@router.post("/edges", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_edge(
    body: CreateEdgeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    graph_service: Annotated[GraphService, Depends(get_graph_service)]
) -> SuccessResponse:
    """
    Manually create or update a directional edge between two memories.
    """
    edge = await graph_service.create_edge(
        user_id=current_user.id,
        data=body,
        created_by="user"
    )
    return SuccessResponse(data=edge)

@router.delete("/edges/{edge_id}", response_model=SuccessResponse)
async def delete_edge(
    edge_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    graph_service: Annotated[GraphService, Depends(get_graph_service)]
) -> SuccessResponse:
    """
    Delete a knowledge edge.
    """
    deleted = await graph_service.delete_edge(edge_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge edge not found"
        )
    return SuccessResponse(data={"deleted": True, "id": str(edge_id)})
