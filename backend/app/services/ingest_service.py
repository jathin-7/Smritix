from __future__ import annotations
import uuid
import os
from datetime import datetime, timezone
from typing import Sequence
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.memory import IngestionJob, Memory, MemoryChunk, MemorySource
from app.repositories.tag_repository import TagRepository
from app.pipelines.extractors import DocumentExtractor
from app.pipelines.chunking import RecursiveCharacterChunker
from app.pipelines.embedding import EmbeddingPipeline
from app.ai.registry import get_embedding_provider, get_llm_provider
from app.core.exceptions import NotFoundError
from app.services.memory_service import MemoryService

class IngestService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tag_repo = TagRepository(session)
        self.chunker = RecursiveCharacterChunker()

    async def create_job(
        self,
        user_id: uuid.UUID,
        source_type: str,
        source_uri: str
    ) -> IngestionJob:
        job = IngestionJob(
            user_id=user_id,
            source_type=source_type,
            source_uri=source_uri,
            status="pending"
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> IngestionJob:
        result = await self.session.execute(
            select(IngestionJob).where(
                IngestionJob.id == job_id,
                IngestionJob.user_id == user_id
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            raise NotFoundError("Ingestion job not found")
        return job

    async def list_jobs(self, user_id: uuid.UUID, limit: int = 50, offset: int = 0) -> Sequence[IngestionJob]:
        result = await self.session.execute(
            select(IngestionJob)
            .where(IngestionJob.user_id == user_id)
            .order_by(IngestionJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def process_document_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
        file_path: str,
        original_filename: str,
        tags: list[str] | None = None
    ) -> None:
        """
        Executes full Phase 2 ingestion pipeline:
        1. Status -> processing
        2. Document extraction
        3. Text chunking
        4. Vector embeddings
        5. AI summarization
        6. Persistent storage as Memory + MemoryChunks + MemorySource
        7. Status -> completed (or failed)
        """
        job = await self.get_job(user_id, job_id)
        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        await self.session.commit()

        try:
            # 1. Content Extraction
            extracted = DocumentExtractor.extract_from_file(file_path, original_filename)
            if not extracted.content.strip():
                raise ValueError("Extracted document content is empty")

            # 2. Recursive Chunking
            chunks = self.chunker.split_text(extracted.content, metadata=extracted.metadata)

            # 3. Embedding Pipeline
            emb_provider = await get_embedding_provider()
            embedding_pipeline = EmbeddingPipeline(emb_provider)
            embedded_chunks = await embedding_pipeline.process_chunks(chunks)

            # 4. AI Summarization
            summary: str | None = None
            try:
                llm = await get_llm_provider()
                prompt = (
                    f"Please provide a concise 2-sentence summary of the following document:\n\n"
                    f"{extracted.content[:3000]}"
                )
                comp = await llm.complete(prompt, max_tokens=150)
                if comp and comp.content:
                    summary = comp.content.strip()
            except Exception:
                # Summary generation is optional post-processing
                summary = extracted.content[:200] + "..."

            # 5. Resolve Tags
            resolved_tags = []
            if tags:
                for t in tags:
                    cleaned = t.strip()
                    if cleaned:
                        tag_entity = await self.tag_repo.get_or_create(user_id, cleaned)
                        resolved_tags.append(tag_entity)

            # 6. Create Memory Entity
            content_hash = MemoryService.compute_content_hash(extracted.content)
            memory = Memory(
                user_id=user_id,
                title=extracted.title,
                content=extracted.content,
                summary=summary,
                memory_type="document",
                source_type="ingested",
                source_uri=original_filename,
                source_metadata=extracted.metadata,
                content_hash=content_hash,
                tags=resolved_tags
            )
            self.session.add(memory)
            await self.session.flush()

            # 7. Create Memory Chunks
            db_chunks = [
                MemoryChunk(
                    memory_id=memory.id,
                    chunk_index=ec.chunk.chunk_index,
                    content=ec.chunk.content,
                    token_count=ec.chunk.token_count,
                    embedding_id=ec.embedding_id,
                    metadata_={
                        "embedding_dimensions": len(ec.embedding),
                        "content_hash": ec.content_hash,
                        "embedding": ec.embedding
                    }
                )
                for ec in embedded_chunks
            ]
            self.session.add_all(db_chunks)

            # 8. Create Memory Source
            source = MemorySource(
                memory_id=memory.id,
                source_type=extracted.metadata.get("format", "document"),
                source_uri=original_filename,
                source_title=extracted.title,
                raw_content_hash=content_hash
            )
            self.session.add(source)

            # 9. Mark Job as Completed
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            # Store memory_id in error_message column or note
            job.error_message = f"Memory ID: {memory.id}"
            await self.session.commit()

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            raise
