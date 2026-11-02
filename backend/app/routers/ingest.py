from __future__ import annotations
import os
import uuid
import shutil
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, Query, status, HTTPException
from app.dependencies import get_ingest_service, get_current_user
from app.services.ingest_service import IngestService
from app.models.user import User
from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.schemas.ingest import IngestionJobResponse, IngestionJobListResponse, IngestTextRequest

settings = get_settings()
router = APIRouter(tags=["ingest"])

ALLOWED_EXTENSIONS = {
    ".pdf", ".md", ".markdown", ".txt", ".text",
    ".py", ".ts", ".js", ".tsx", ".jsx", ".json", ".csv", ".html"
}

async def run_document_ingestion_background(
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    file_path: str,
    original_filename: str,
    tags: list[str] | None,
) -> None:
    async with AsyncSessionLocal() as session:
        service = IngestService(session)
        try:
            await service.process_document_job(
                job_id=job_id,
                user_id=user_id,
                file_path=file_path,
                original_filename=original_filename,
                tags=tags
            )
        except Exception:
            # Errors are recorded directly on the IngestionJob record
            pass

@router.post("/document", response_model=IngestionJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tags: str | None = Form(None),
    ingest_service: Annotated[IngestService, Depends(get_ingest_service)] = None, # type: ignore
    current_user: Annotated[User, Depends(get_current_user)] = None, # type: ignore
) -> IngestionJobResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{ext}' is not supported. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Ensure upload directory exists
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save to disk with unique prefix
    safe_filename = f"{uuid.uuid4()}_{file.filename}"
    saved_path = upload_dir / safe_filename

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Check file size limit
    file_size_mb = saved_path.stat().st_size / (1024 * 1024)
    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

    # Create Job record
    job = await ingest_service.create_job(
        user_id=current_user.id,
        source_type="file",
        source_uri=file.filename
    )

    # Dispatch to background task execution
    background_tasks.add_task(
        run_document_ingestion_background,
        job_id=job.id,
        user_id=current_user.id,
        file_path=str(saved_path),
        original_filename=file.filename,
        tags=tag_list
    )

    return IngestionJobResponse.model_validate(job)

@router.get("/jobs", response_model=IngestionJobListResponse)
async def list_jobs(
    ingest_service: Annotated[IngestService, Depends(get_ingest_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> IngestionJobListResponse:
    jobs = await ingest_service.list_jobs(current_user.id, limit=limit, offset=offset)
    items = [IngestionJobResponse.model_validate(j) for j in jobs]
    return IngestionJobListResponse(items=items, total=len(items))

@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
async def get_job(
    job_id: uuid.UUID,
    ingest_service: Annotated[IngestService, Depends(get_ingest_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> IngestionJobResponse:
    job = await ingest_service.get_job(current_user.id, job_id)
    return IngestionJobResponse.model_validate(job)
