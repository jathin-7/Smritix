from __future__ import annotations
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class PaginationParams(BaseModel):
    cursor: str | None = None
    limit: int = Field(default=20, le=100)

class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: dict[str, Any]

class SuccessResponse(BaseModel):
    data: Any
    meta: dict[str, Any] = Field(default_factory=dict)

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[Any] | None = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
    meta: dict[str, Any] = Field(default_factory=dict)

class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict[str, str] = Field(default_factory=dict)
