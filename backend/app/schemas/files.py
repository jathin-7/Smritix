from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

# Root Schemas
class RegisterRootRequest(BaseModel):
    root_path: str = Field(..., min_length=1)
    display_name: str | None = None
    is_monitored: bool = True

class FileRootResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    root_path: str
    display_name: str
    is_monitored: bool
    last_scanned_at: datetime | None
    created_at: datetime
    updated_at: datetime
    file_count: int = 0
    indexed_count: int = 0

    class Config:
        from_attributes = True

# File Record Schemas
class FileRecordResponse(BaseModel):
    id: uuid.UUID
    root_id: uuid.UUID
    user_id: uuid.UUID
    relative_path: str
    absolute_path: str
    file_name: str
    extension: str
    file_size: int
    content_hash: str | None
    modified_at: datetime
    indexed_at: datetime | None
    indexing_status: str
    error_message: str | None
    is_starred: bool
    created_at: datetime
    updated_at: datetime
    chunk_count: int = 0

    class Config:
        from_attributes = True

class FileChunkResponse(BaseModel):
    id: uuid.UUID
    file_id: uuid.UUID
    chunk_index: int
    page_number: int | None
    section_heading: str | None
    content: str
    token_count: int | None

    class Config:
        from_attributes = True

class FileListResponse(BaseModel):
    items: list[FileRecordResponse]
    total: int
    page: int
    limit: int

class FileScanResult(BaseModel):
    root_id: uuid.UUID
    files_discovered: int
    files_new: int
    files_modified: int
    files_deleted: int
    jobs_queued: int

class FileReindexResponse(BaseModel):
    file_id: uuid.UUID
    status: str
    message: str

class FileEventRequest(BaseModel):
    root_path: str
    file_path: str
    event_type: str # created, modified, deleted, renamed
    old_path: str | None = None

class FileSearchRequest(BaseModel):
    query: str
    root_id: uuid.UUID | None = None
    extension: str | None = None
    limit: int = 10

class FileSearchResultItem(BaseModel):
    file_id: uuid.UUID
    file_name: str
    relative_path: str
    absolute_path: str
    extension: str
    chunk_index: int
    page_number: int | None
    section_heading: str | None
    snippet: str
    score: float

class FileSearchResponse(BaseModel):
    query: str
    items: list[FileSearchResultItem]
    total: int

class StorageOverviewResponse(BaseModel):
    total_approved_roots: int
    total_monitored_folders: int
    total_files: int
    total_indexed_files: int
    total_indexed_chunks: int
    total_bytes_tracked: int
    supported_extensions: list[str]
    recent_jobs: list[dict[str, Any]]
