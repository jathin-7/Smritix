from __future__ import annotations
import uuid
import hashlib
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.memory_repository import MemoryRepository
from app.repositories.tag_repository import TagRepository
from app.models.memory import Memory, MemoryChunk
from app.schemas.memory import CreateMemoryRequest, UpdateMemoryRequest
from app.core.exceptions import NotFoundError
from app.pipelines.chunking import RecursiveCharacterChunker, TextChunk
from app.pipelines.embedding import EmbeddingPipeline
from app.ai.registry import get_embedding_provider

class MemoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.memory_repo = MemoryRepository(session)
        self.tag_repo = TagRepository(session)

    @staticmethod
    def compute_content_hash(content: str) -> str:
        return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()

    async def create_memory(self, user_id: uuid.UUID, data: CreateMemoryRequest) -> Memory:
        content_hash = self.compute_content_hash(data.content)
        title = data.title.strip() if data.title else data.content.strip().split("\n")[0][:80]

        # Resolve tags
        tags = []
        if data.tags:
            for tag_name in data.tags:
                if tag_name.strip():
                    tag = await self.tag_repo.get_or_create(user_id, tag_name.strip())
                    tags.append(tag)

        # Create memory entity
        memory = Memory(
            user_id=user_id,
            title=title,
            content=data.content,
            summary=None,
            memory_type=data.memory_type,
            source_type=data.source_type,
            source_uri=data.source_uri,
            content_hash=content_hash,
            tags=tags
        )
        self.session.add(memory)
        await self.session.flush()

        # Split into semantic chunks
        chunker = RecursiveCharacterChunker()
        text_chunks = chunker.split_text(data.content)
        if not text_chunks:
            text_chunks = [
                TextChunk(
                    chunk_index=0,
                    content=data.content,
                    token_count=len(data.content.split())
                )
            ]

        # Generate vector embeddings
        try:
            emb_provider = await get_embedding_provider()
            embedding_pipeline = EmbeddingPipeline(emb_provider)
            embedded_chunks = await embedding_pipeline.process_chunks(text_chunks)
            db_chunks = [
                MemoryChunk(
                    memory_id=memory.id,
                    chunk_index=ec.chunk.chunk_index,
                    content=ec.chunk.content,
                    token_count=ec.chunk.token_count,
                    embedding_id=ec.embedding_id,
                    metadata_={
                        "embedding": ec.embedding,
                        "content_hash": ec.content_hash
                    }
                )
                for ec in embedded_chunks
            ]
        except Exception:
            db_chunks = [
                MemoryChunk(
                    memory_id=memory.id,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    token_count=c.token_count
                )
                for c in text_chunks
            ]

        self.session.add_all(db_chunks)

        await self.session.commit()

        # Phase 5: Auto-connection discovery in knowledge graph
        try:
            from app.services.graph_service import GraphService
            graph_service = GraphService(self.session)
            await graph_service.discover_and_create_connections(user_id, memory.id, threshold=0.65)
        except Exception:
            pass

        return await self.get_memory(memory.id, user_id)

    async def get_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> Memory:
        memory = await self.memory_repo.get_by_id_loaded(memory_id, user_id)
        if not memory:
            raise NotFoundError("Memory not found")
        return memory

    async def list_memories(
        self,
        user_id: uuid.UUID,
        memory_type: str | None = None,
        tag_name: str | None = None,
        query: str | None = None,
        is_archived: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[Sequence[Memory], int]:
        return await self.memory_repo.list_memories(
            user_id=user_id,
            memory_type=memory_type,
            tag_name=tag_name,
            query_text=query,
            is_archived=is_archived,
            limit=limit,
            offset=offset
        )

    async def update_memory(
        self,
        memory_id: uuid.UUID,
        user_id: uuid.UUID,
        data: UpdateMemoryRequest
    ) -> Memory:
        memory = await self.memory_repo.get_by_id_loaded(memory_id, user_id)
        if not memory:
            raise NotFoundError("Memory not found")

        if data.title is not None:
            memory.title = data.title.strip()
        if data.content is not None:
            memory.content = data.content
            memory.content_hash = self.compute_content_hash(data.content)
        if data.summary is not None:
            memory.summary = data.summary
        if data.memory_type is not None:
            memory.memory_type = data.memory_type
        if data.tags is not None:
            resolved_tags = []
            for tag_name in data.tags:
                cleaned = tag_name.strip()
                if cleaned:
                    tag = await self.tag_repo.get_or_create(user_id, cleaned)
                    resolved_tags.append(tag)
            memory.tags = resolved_tags

        await self.session.commit()
        return await self.get_memory(memory_id, user_id)

    async def delete_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        deleted = await self.memory_repo.soft_delete(memory_id, user_id)
        if not deleted:
            raise NotFoundError("Memory not found")
        await self.session.commit()
        return True

    async def archive_memory(self, memory_id: uuid.UUID, user_id: uuid.UUID, archived: bool = True) -> Memory:
        memory = await self.memory_repo.set_archived(memory_id, user_id, archived)
        if not memory:
            raise NotFoundError("Memory not found")
        await self.session.commit()
        return await self.get_memory(memory_id, user_id)
