from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user, get_dashboard_service
from app.models.user import User
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import (
    DashboardStatsResponse,
    TimelineResponse,
    KnowledgeGapsResponse
)
from app.schemas.common import SuccessResponse

router = APIRouter(tags=["dashboard"])

@router.get("/stats", response_model=SuccessResponse)
async def get_dashboard_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)]
) -> SuccessResponse:
    """
    Retrieve aggregated dashboard statistics: counts, type breakdown, activity sparkline, top tags.
    """
    stats = await dashboard_service.get_stats(current_user.id)
    return SuccessResponse(data=stats)

@router.get("/timeline", response_model=SuccessResponse)
async def get_dashboard_timeline(
    current_user: Annotated[User, Depends(get_current_user)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    limit: int = Query(default=50, ge=1, le=200)
) -> SuccessResponse:
    """
    Retrieve chronological memory timeline grouped by calendar date.
    """
    timeline = await dashboard_service.get_timeline(current_user.id, limit=limit)
    return SuccessResponse(data=timeline)

@router.get("/knowledge-gaps", response_model=SuccessResponse)
async def get_knowledge_gaps(
    current_user: Annotated[User, Depends(get_current_user)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)]
) -> SuccessResponse:
    """
    Identify orphaned or unclassified memories to strengthen the personal knowledge graph.
    """
    gaps = await dashboard_service.get_knowledge_gaps(current_user.id)
    return SuccessResponse(data=gaps)
