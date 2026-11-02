from __future__ import annotations
import uuid
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete

from app.models.file_record import FileRecord, FileChunk, FileJob
from app.services.file_intelligence.extractor import FileExtractionService
from app.services.file_intelligence.chunker import FileChunkingService
from app.services.vector_store import VectorStoreService
from app.ai.registry import get_embedding_provider

class FileIndexingService:
    def __init__(self, session: AsyncSession, vector_store: VectorStoreService | None = None):
        self.session = session
        self.vector_store = vector_store or VectorStoreService()
        self.chunker = FileChunkingService(target_chunk_size=700, overlap=100)

    async def index_file(self, user_id: uuid.UUID, file_id: uuid.UUID) -> bool:
        # Load file record
        res = await self.session.execute(
            select(FileRecord).where(
                and_(FileRecord.user_id == user_id, FileRecord.id == file_id)
            )
        )
        file_rec = res.scalars().first()
        if not file_rec:
            return False

        file_rec.indexing_status = "indexing"
        file_rec.error_message = None
        await self.session.commit()

        try:
            path = Path(file_rec.absolute_path)
            if not path.exists():
                file_rec.indexing_status = "failed"
                file_rec.error_message = "File does not exist on filesystem"
                await self.session.commit()
                return False

            # 1. Extract Document Content
            extracted_doc = FileExtractionService.extract(path)
            if not extracted_doc.content.strip():
                file_rec.indexing_status = "skipped"
                file_rec.error_message = "File contains no extractable text content"
                await self.session.commit()
                return True

            # 2. Chunk Document Content
            text_chunks = self.chunker.chunk_document(extracted_doc)
            if not text_chunks:
                file_rec.indexing_status = "skipped"
                file_rec.error_message = "No chunks generated"
                await self.session.commit()
                return True

            # 3. Generate Embeddings using existing pipeline
            emb_provider = await get_embedding_provider()
            chunk_texts = [c.content for c in text_chunks]
            embeddings = await emb_provider.embed(chunk_texts)

            # 4. Remove previous chunks for this file
            await self.session.execute(
                delete(FileChunk).where(FileChunk.file_id == file_id)
            )

            # 5. Store FileChunks & prepare Vector Store points
            db_chunks: list[FileChunk] = []
            vector_points: list[dict] = []

            for idx, (chunk, emb) in enumerate(zip(text_chunks, embeddings)):
                emb_id = str(uuid.uuid4())
                fc = FileChunk(
                    file_id=file_id,
                    user_id=user_id,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    section_heading=chunk.section_heading,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    embedding_id=emb_id,
                    metadata_json={
                        **chunk.metadata,
                        "file_name": file_rec.file_name,
                        "relative_path": file_rec.relative_path,
                        "extension": file_rec.extension,
                        "embedding": emb  # Stored in chunk metadata for fallback cosine similarity
                    }
                )
                db_chunks.append(fc)
                self.session.add(fc)

                vector_points.append({
                    "id": emb_id,
                    "vector": emb,
                    "payload": {
                        "type": "file_chunk",
                        "file_id": str(file_id),
                        "user_id": str(user_id),
                        "file_name": file_rec.file_name,
                        "relative_path": file_rec.relative_path,
                        "extension": file_rec.extension,
                        "chunk_index": chunk.chunk_index,
                        "page_number": chunk.page_number,
                        "section_heading": chunk.section_heading,
                        "content": chunk.content[:400],
                    }
                })

            # 6. Upsert into Qdrant if available
            try:
                if await self.vector_store.is_available() and embeddings:
                    dim = len(embeddings[0])
                    await self.vector_store.ensure_collection(dim)
                    await self.vector_store.upsert_points(vector_points)
            except Exception:
                pass  # Portable DB fallback preserves embeddings in chunk metadata

            # 7. Finalize Status
            file_rec.indexing_status = "indexed"
            file_rec.indexed_at = datetime.now(timezone.utc)
            file_rec.error_message = None
            await self.session.commit()
            return True

        except Exception as e:
            file_rec.indexing_status = "failed"
            file_rec.error_message = str(e)[:500]
            await self.session.commit()
            return False

    async def remove_index(self, user_id: uuid.UUID, file_id: uuid.UUID) -> bool:
        res = await self.session.execute(
            select(FileRecord).where(
                and_(FileRecord.user_id == user_id, FileRecord.id == file_id)
            )
        )
        file_rec = res.scalars().first()
        if not file_rec:
            return False

        # Delete database chunks
        await self.session.execute(
            delete(FileChunk).where(FileChunk.file_id == file_id)
        )
        file_rec.indexing_status = "pending"
        file_rec.indexed_at = None
        await self.session.commit()
        return True
