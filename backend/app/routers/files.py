from __future__ import annotations
import uuid
from typing import Annotated, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.files import (
    RegisterRootRequest,
    FileRootResponse,
    FileRecordResponse,
    FileListResponse,
    FileScanResult,
    FileReindexResponse,
    FileEventRequest,
    FileSearchRequest,
    FileSearchResponse,
    FileSearchResultItem,
    StorageOverviewResponse
)
from app.services.file_intelligence.registry import FileRegistryService
from app.services.file_intelligence.indexer import FileIndexingService
from app.services.file_intelligence.sync import FileSyncService
from app.services.search_service import SearchService

router = APIRouter(tags=["files"])

def format_root_response(root: FileRoot, file_count: int = 0, indexed_count: int = 0) -> FileRootResponse:
    return FileRootResponse(
        id=root.id,
        user_id=root.user_id,
        root_path=root.root_path,
        display_name=root.display_name,
        is_monitored=root.is_monitored,
        last_scanned_at=root.last_scanned_at,
        created_at=root.created_at,
        updated_at=root.updated_at,
        file_count=file_count,
        indexed_count=indexed_count
    )

def format_file_response(f: FileRecord, chunk_count: int = 0) -> FileRecordResponse:
    return FileRecordResponse(
        id=f.id,
        root_id=f.root_id,
        user_id=f.user_id,
        relative_path=f.relative_path,
        absolute_path=f.absolute_path,
        file_name=f.file_name,
        extension=f.extension,
        file_size=f.file_size,
        content_hash=f.content_hash,
        modified_at=f.modified_at,
        indexed_at=f.indexed_at,
        indexing_status=f.indexing_status,
        error_message=f.error_message,
        is_starred=f.is_starred,
        created_at=f.created_at,
        updated_at=f.updated_at,
        chunk_count=chunk_count
    )

@router.post("/roots", response_model=FileRootResponse, status_code=status.HTTP_201_CREATED)
async def register_root(
    data: RegisterRootRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> FileRootResponse:
    registry = FileRegistryService(db)
    root = await registry.register_root(
        user_id=current_user.id,
        root_path=data.root_path,
        display_name=data.display_name,
        is_monitored=data.is_monitored
    )
    # Trigger initial scan
    stats = await registry.scan_root(current_user.id, root.id)
    return format_root_response(root, file_count=stats["discovered"], indexed_count=0)

@router.get("/roots", response_model=list[FileRootResponse])
async def list_roots(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> list[FileRootResponse]:
    registry = FileRegistryService(db)
    roots = await registry.list_roots(current_user.id)
    result: list[FileRootResponse] = []
    for r in roots:
        result.append(format_root_response(r, file_count=0, indexed_count=0))
    return result

@router.delete("/roots/{root_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_root(
    root_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    registry = FileRegistryService(db)
    success = await registry.delete_root(current_user.id, root_id)
    if not success:
        return

@router.post("/roots/{root_id}/scan", response_model=FileScanResult)
async def scan_root(
    root_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> FileScanResult:
    registry = FileRegistryService(db)
    indexer = FileIndexingService(db)
    stats = await registry.scan_root(current_user.id, root_id)

    # Automatically index pending files discovered
    pending_files, _ = await registry.list_files(
        user_id=current_user.id,
        root_id=root_id,
        indexing_status="pending",
        limit=50
    )
    jobs_count = 0
    for f in pending_files:
        await indexer.index_file(current_user.id, f.id)
        jobs_count += 1

    return FileScanResult(
        root_id=root_id,
        files_discovered=stats["discovered"],
        files_new=stats["new"],
        files_modified=stats["modified"],
        files_deleted=stats["deleted"],
        jobs_queued=jobs_count
    )

@router.get("", response_model=FileListResponse)
async def list_files(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    root_id: uuid.UUID | None = None,
    extension: str | None = None,
    indexing_status: str | None = None,
    search: str | None = None,
    is_starred: bool | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200)
) -> FileListResponse:
    registry = FileRegistryService(db)
    skip = (page - 1) * limit
    files, total = await registry.list_files(
        user_id=current_user.id,
        root_id=root_id,
        extension=extension,
        indexing_status=indexing_status,
        search_query=search,
        is_starred=is_starred,
        skip=skip,
        limit=limit
    )

    items = []
    for f in files:
        chunk_c = len(f.chunks) if hasattr(f, "chunks") and f.chunks else 0
        items.append(format_file_response(f, chunk_count=chunk_c))

    return FileListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit
    )

@router.get("/storage/overview", response_model=StorageOverviewResponse)
async def storage_overview(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> StorageOverviewResponse:
    sync_svc = FileSyncService(db)
    stats = await sync_svc.get_storage_overview(current_user.id)
    return StorageOverviewResponse(**stats)

@router.get("/{file_id}", response_model=FileRecordResponse)
async def get_file_detail(
    file_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> FileRecordResponse:
    registry = FileRegistryService(db)
    f = await registry.get_file(current_user.id, file_id)
    if not f:
        raise ValueError("File not found")
    chunk_c = len(f.chunks) if hasattr(f, "chunks") and f.chunks else 0
    return format_file_response(f, chunk_count=chunk_c)

@router.post("/{file_id}/reindex", response_model=FileReindexResponse)
async def reindex_file(
    file_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> FileReindexResponse:
    indexer = FileIndexingService(db)
    success = await indexer.index_file(current_user.id, file_id)
    return FileReindexResponse(
        file_id=file_id,
        status="completed" if success else "failed",
        message="File reindexed successfully" if success else "Indexing failed or file contains no text"
    )

@router.delete("/{file_id}/index", response_model=FileReindexResponse)
async def remove_file_index(
    file_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> FileReindexResponse:
    indexer = FileIndexingService(db)
    await indexer.remove_index(current_user.id, file_id)
    return FileReindexResponse(
        file_id=file_id,
        status="removed",
        message="File vector index removed"
    )

@router.post("/{file_id}/star")
async def toggle_star(
    file_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict[str, Any]:
    registry = FileRegistryService(db)
    starred = await registry.toggle_star(current_user.id, file_id)
    return {"file_id": file_id, "is_starred": starred}

@router.post("/events")
async def handle_file_event(
    event: FileEventRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict[str, Any]:
    sync_svc = FileSyncService(db)
    processed = await sync_svc.handle_file_event(
        user_id=current_user.id,
        root_path=event.root_path,
        file_path=event.file_path,
        event_type=event.event_type,
        old_path=event.old_path
    )
    return {"status": "ok", "processed": processed}
