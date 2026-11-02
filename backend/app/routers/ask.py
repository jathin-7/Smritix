from __future__ import annotations
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.dependencies import get_current_user, get_rag_service
from app.models.user import User
from app.services.rag_service import RAGService
from app.schemas.ask import (
    AskRequest,
    AskResponse,
    ConversationItemResponse,
    ConversationDetailResponse
)
from app.schemas.common import SuccessResponse

router = APIRouter(tags=["ask"])

@router.post("", response_model=SuccessResponse)
@router.post("/", response_model=SuccessResponse)
async def ask_question(
    body: AskRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> SuccessResponse:
    """
    Query personal memory store and generate an AI answer citing memory sources.
    """
    res = await rag_service.ask(
        user_id=current_user.id,
        query=body.query,
        conversation_id=body.conversation_id,
        limit=body.limit
    )
    return SuccessResponse(data=res)

@router.post("/stream")
async def ask_question_stream(
    body: AskRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> StreamingResponse:
    """
    Stream AI memory answer with citations via Server-Sent Events (SSE).
    """
    return StreamingResponse(
        rag_service.ask_stream(
            user_id=current_user.id,
            query=body.query,
            conversation_id=body.conversation_id,
            limit=body.limit
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/conversations", response_model=SuccessResponse)
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> SuccessResponse:
    """
    List user's RAG conversations ordered by most recent activity.
    """
    conversations = await rag_service.list_conversations(current_user.id)
    return SuccessResponse(data=conversations)

@router.get("/conversations/{conversation_id}", response_model=SuccessResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> SuccessResponse:
    """
    Retrieve full conversation message history and cited source memory items.
    """
    detail = await rag_service.get_conversation_detail(conversation_id, current_user.id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return SuccessResponse(data=detail)

@router.delete("/conversations/{conversation_id}", response_model=SuccessResponse)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> SuccessResponse:
    """
    Delete a conversation and its messages.
    """
    deleted = await rag_service.delete_conversation(conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return SuccessResponse(data={"deleted": True, "id": str(conversation_id)})
