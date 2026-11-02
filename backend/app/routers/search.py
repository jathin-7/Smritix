from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from app.dependencies import get_search_service, get_current_user
from app.services.search_service import SearchService
from app.models.user import User
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchHistoryResponse,
    SearchHistoryItem
)

router = APIRouter(tags=["search"])

@router.post("/", response_model=SearchResponse)
async def semantic_search(
    data: SearchRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SearchResponse:
    results = await search_service.semantic_search(
        user_id=current_user.id,
        query=data.query,
        limit=data.limit,
        memory_type=data.memory_type,
        tag=data.tag,
        min_score=data.min_score
    )
    # Record in history
    await search_service.record_search(
        user_id=current_user.id,
        query=data.query,
        search_type="semantic",
        results_count=len(results)
    )
    return SearchResponse(
        query=data.query,
        search_type="semantic",
        results=results,
        total=len(results)
    )

@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    data: SearchRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SearchResponse:
    results = await search_service.hybrid_search(
        user_id=current_user.id,
        query=data.query,
        limit=data.limit,
        memory_type=data.memory_type,
        tag=data.tag,
        min_score=data.min_score
    )
    # Record in history
    await search_service.record_search(
        user_id=current_user.id,
        query=data.query,
        search_type="hybrid",
        results_count=len(results)
    )
    return SearchResponse(
        query=data.query,
        search_type="hybrid",
        results=results,
        total=len(results)
    )

@router.get("/history", response_model=SearchHistoryResponse)
async def get_search_history(
    search_service: Annotated[SearchService, Depends(get_search_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(20, ge=1, le=100),
) -> SearchHistoryResponse:
    history = await search_service.get_search_history(current_user.id, limit=limit)
    items = [SearchHistoryItem.model_validate(h) for h in history]
    return SearchHistoryResponse(items=items, total=len(items))
