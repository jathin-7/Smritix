from __future__ import annotations
from fastapi import APIRouter

router = APIRouter(tags=["voice"])

@router.get("/")
async def voice_status() -> dict[str, str]:
    return {"message": "voice endpoint - coming soon"}
