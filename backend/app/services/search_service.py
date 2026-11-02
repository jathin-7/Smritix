from __future__ import annotations
import math
import uuid
from typing import Sequence, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from app.models.memory import Memory, MemoryChunk, Tag, SearchHistory
from app.models.file_record import FileRecord, FileChunk
from app.services.vector_store import VectorStoreService
from app.ai.registry import get_embedding_provider
from app.schemas.search import SearchResultItem
from app.schemas.files import FileSearchResultItem

class SearchService:
    def __init__(self, session: AsyncSession, vector_store: VectorStoreService | None = None):
        self.session = session
        self.vector_store = vector_store or VectorStoreService()

    @staticmethod
    def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def record_search(
        self,
        user_id: uuid.UUID,
        query: str,
        search_type: str = "hybrid",
        results_count: int = 0
    ) -> SearchHistory:
        history = SearchHistory(
            user_id=user_id,
            query=query.strip(),
            search_type=search_type,
            results_count=results_count
        )
        self.session.add(history)
        await self.session.commit()
        return history

    async def get_search_history(self, user_id: uuid.UUID, limit: int = 20) -> Sequence[SearchHistory]:
        result = await self.session.execute(
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def semantic_search(
        self,
        user_id: uuid.UUID,
        query: str,
        limit: int = 10,
        memory_type: str | None = None,
        tag: str | None = None,
        min_score: float = 0.0
    ) -> list[SearchResultItem]:
        emb_provider = await get_embedding_provider()
        query_vectors = await emb_provider.embed([query])
        if not query_vectors:
            return []
        query_vector = query_vectors[0]

        # 1. Try Qdrant if available
        qdrant_results = await self.vector_store.search(
            query_vector=query_vector,
            user_id=user_id,
            limit=limit * 2,
            memory_type=memory_type
        )

        if qdrant_results:
            items: list[SearchResultItem] = []
            for r in qdrant_results:
                if r["score"] < min_score:
                    continue
                if tag and tag not in r.get("tags", []):
                    continue
                items.append(
                    SearchResultItem(
                        memory_id=uuid.UUID(str(r["memory_id"])),
                        title=r.get("title"),
                        snippet=r.get("content", "")[:300],
                        memory_type=r.get("memory_type", "note"),
                        score=round(r["score"], 4),
                        tags=r.get("tags", []),
                        chunk_index=r.get("chunk_index"),
                        created_at=func.now() # populated below if loaded
                    )
                )
            if items:
                return items[:limit]

        # 2. Portable database fallback: compute vector similarity against stored chunks
        stmt = (
            select(MemoryChunk)
            .join(Memory, MemoryChunk.memory_id == Memory.id)
            .where(
                Memory.user_id == user_id,
                Memory.is_deleted.is_(False),
                Memory.is_archived.is_(False)
            )
            .options(
                selectinload(MemoryChunk.memory).selectinload(Memory.tags)
            )
        )
        if memory_type:
            stmt = stmt.where(Memory.memory_type == memory_type)
        if tag:
            stmt = stmt.join(Memory.tags).where(Tag.name == tag.strip())

        res = await self.session.execute(stmt)
        chunks = res.scalars().all()

        scored_items: list[tuple[float, MemoryChunk]] = []
        for c in chunks:
            meta = c.metadata_ or {}
            chunk_vec = meta.get("embedding")
            if not chunk_vec:
                try:
                    vecs = await emb_provider.embed([c.content])
                    if vecs:
                        chunk_vec = vecs[0]
                except Exception:
                    pass
            if chunk_vec:
                score = self.cosine_similarity(query_vector, chunk_vec)
                if score >= min_score:
                    scored_items.append((score, c))

        scored_items.sort(key=lambda x: x[0], reverse=True)

        # Deduplicate per memory (keep best matching chunk per memory)
        seen_memories: set[uuid.UUID] = set()
        results: list[SearchResultItem] = []

        for score, chunk in scored_items:
            m = chunk.memory
            if m.id in seen_memories:
                continue
            seen_memories.add(m.id)
            tag_names = [t.name for t in m.tags] if m.tags else []

            results.append(
                SearchResultItem(
                    memory_id=m.id,
                    title=m.title,
                    snippet=chunk.content[:300],
                    memory_type=m.memory_type,
                    score=round(score, 4),
                    tags=tag_names,
                    chunk_index=chunk.chunk_index,
                    created_at=m.created_at
                )
            )
            if len(results) >= limit:
                break

        return results

    async def keyword_search(
        self,
        user_id: uuid.UUID,
        query: str,
        limit: int = 10,
        memory_type: str | None = None,
        tag: str | None = None
    ) -> list[SearchResultItem]:
        pattern = f"%{query.strip()}%"

        stmt = (
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.is_deleted.is_(False),
                Memory.is_archived.is_(False),
                or_(
                    Memory.title.ilike(pattern),
                    Memory.content.ilike(pattern),
                    Memory.summary.ilike(pattern)
                )
            )
            .options(
                selectinload(Memory.tags),
                selectinload(Memory.chunks)
            )
        )
        if memory_type:
            stmt = stmt.where(Memory.memory_type == memory_type)
        if tag:
            stmt = stmt.join(Memory.tags).where(Tag.name == tag.strip())

        res = await self.session.execute(stmt.limit(limit * 2))
        memories = res.scalars().all()

        query_lower = query.lower().strip()
        results: list[SearchResultItem] = []

        for m in memories:
            # Score relevance based on title/summary/content match
            score = 0.5
            title_lower = (m.title or "").lower()
            if query_lower in title_lower:
                score += 0.4
            if m.summary and query_lower in m.summary.lower():
                score += 0.2

            # Find matching snippet from chunks or content
            snippet = m.content[:300]
            chunk_idx = None
            if m.chunks:
                for c in m.chunks:
                    if query_lower in c.content.lower():
                        snippet = c.content[:300]
                        chunk_idx = c.chunk_index
                        break

            tag_names = [t.name for t in m.tags] if m.tags else []
            results.append(
                SearchResultItem(
                    memory_id=m.id,
                    title=m.title,
                    snippet=snippet,
                    memory_type=m.memory_type,
                    score=round(min(1.0, score), 4),
                    tags=tag_names,
                    chunk_index=chunk_idx,
                    created_at=m.created_at
                )
            )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    async def hybrid_search(
        self,
        user_id: uuid.UUID,
        query: str,
        limit: int = 10,
        memory_type: str | None = None,
        tag: str | None = None,
        min_score: float = 0.0
    ) -> list[SearchResultItem]:
        """
        Reciprocal Rank Fusion (RRF) combining dense semantic search + full-text keyword search:
        RRF_Score(d) = 1/(60 + r_semantic(d)) + 1/(60 + r_keyword(d))
        """
        semantic_results = await self.semantic_search(
            user_id=user_id,
            query=query,
            limit=limit * 2,
            memory_type=memory_type,
            tag=tag,
            min_score=min_score
        )
        keyword_results = await self.keyword_search(
            user_id=user_id,
            query=query,
            limit=limit * 2,
            memory_type=memory_type,
            tag=tag
        )

        rrf_k = 60.0
        scores: dict[uuid.UUID, float] = {}
        items_map: dict[uuid.UUID, SearchResultItem] = {}

        for rank, item in enumerate(semantic_results):
            mid = item.memory_id
            items_map[mid] = item
            scores[mid] = scores.get(mid, 0.0) + (1.0 / (rrf_k + rank + 1))

        for rank, item in enumerate(keyword_results):
            mid = item.memory_id
            if mid not in items_map:
                items_map[mid] = item
            scores[mid] = scores.get(mid, 0.0) + (1.0 / (rrf_k + rank + 1))

        if not scores:
            return []

        # Normalize max RRF score to 1.0 scale
        max_rrf = max(scores.values()) or 1.0
        sorted_mids = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)

        final_results: list[SearchResultItem] = []
        for mid in sorted_mids[:limit]:
            item = items_map[mid]
            normalized_score = round(scores[mid] / max_rrf, 4)
            final_results.append(
                SearchResultItem(
                    memory_id=item.memory_id,
                    title=item.title,
                    snippet=item.snippet,
                    memory_type=item.memory_type,
                    score=normalized_score,
                    tags=item.tags,
                    chunk_index=item.chunk_index,
                    created_at=item.created_at
                )
            )

        return final_results

    async def search_files(
        self,
        user_id: uuid.UUID,
        query: str,
        limit: int = 10,
        min_score: float = 0.0
    ) -> list[FileSearchResultItem]:
        emb_provider = await get_embedding_provider()
        query_vectors = await emb_provider.embed([query])
        if not query_vectors:
            return []
        query_vector = query_vectors[0]

        stmt = (
            select(FileChunk)
            .join(FileRecord, FileChunk.file_id == FileRecord.id)
            .where(
                FileChunk.user_id == user_id,
                FileRecord.indexing_status == "indexed"
            )
            .options(selectinload(FileChunk.file))
        )
        res = await self.session.execute(stmt)
        chunks = res.scalars().all()

        scored: list[tuple[float, FileChunk]] = []
        q_lower = query.lower()

        for c in chunks:
            meta = c.metadata_json or {}
            chunk_vec = meta.get("embedding")
            if not chunk_vec:
                try:
                    vecs = await emb_provider.embed([c.content])
                    if vecs:
                        chunk_vec = vecs[0]
                except Exception:
                    pass
            if chunk_vec:
                score = self.cosine_similarity(query_vector, chunk_vec)
                if c.file and q_lower in c.file.file_name.lower():
                    score += 0.15
                if c.section_heading and q_lower in c.section_heading.lower():
                    score += 0.1
                if q_lower in c.content.lower():
                    score += 0.08

                if score >= min_score:
                    scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)

        results: list[FileSearchResultItem] = []
        for score, chunk in scored[:limit]:
            f = chunk.file
            results.append(
                FileSearchResultItem(
                    file_id=chunk.file_id,
                    file_name=f.file_name if f else "Unknown file",
                    relative_path=f.relative_path if f else "",
                    absolute_path=f.absolute_path if f else "",
                    extension=f.extension if f else "",
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    section_heading=chunk.section_heading,
                    snippet=chunk.content[:350],
                    score=round(min(score, 1.0), 4)
                )
            )
        return results
