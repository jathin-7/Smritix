from __future__ import annotations
import uuid
from typing import Sequence, Any
from sqlalchemy import select, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph import KnowledgeEdge
from app.repositories.base import BaseRepository

class GraphRepository(BaseRepository[KnowledgeEdge]):
    def __init__(self, session: AsyncSession):
        super().__init__(KnowledgeEdge, session)

    async def get_edge(
        self,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        relation_type: str,
        user_id: uuid.UUID
    ) -> KnowledgeEdge | None:
        stmt = select(KnowledgeEdge).where(
            KnowledgeEdge.user_id == user_id,
            KnowledgeEdge.source_memory_id == source_id,
            KnowledgeEdge.target_memory_id == target_id,
            KnowledgeEdge.relation_type == relation_type
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_or_update_edge(
        self,
        user_id: uuid.UUID,
        source_memory_id: uuid.UUID,
        target_memory_id: uuid.UUID,
        relation_type: str,
        confidence: float = 1.0,
        created_by: str = "user",
        metadata: dict[str, Any] | None = None
    ) -> KnowledgeEdge:
        existing = await self.get_edge(source_memory_id, target_memory_id, relation_type, user_id)
        if existing:
            existing.confidence = confidence
            existing.created_by = created_by
            if metadata:
                existing.metadata_ = metadata
            await self.session.flush()
            return existing

        edge = KnowledgeEdge(
            user_id=user_id,
            source_memory_id=source_memory_id,
            target_memory_id=target_memory_id,
            relation_type=relation_type,
            confidence=confidence,
            created_by=created_by,
            metadata_=metadata or {}
        )
        self.session.add(edge)
        await self.session.flush()
        return edge

    async def get_edge_by_id(self, edge_id: uuid.UUID, user_id: uuid.UUID) -> KnowledgeEdge | None:
        stmt = select(KnowledgeEdge).where(
            KnowledgeEdge.id == edge_id,
            KnowledgeEdge.user_id == user_id
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete_edge(self, edge_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = delete(KnowledgeEdge).where(
            KnowledgeEdge.id == edge_id,
            KnowledgeEdge.user_id == user_id
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0

    async def get_user_edges(
        self,
        user_id: uuid.UUID,
        min_confidence: float = 0.0,
        limit: int = 500
    ) -> Sequence[KnowledgeEdge]:
        stmt = (
            select(KnowledgeEdge)
            .where(
                KnowledgeEdge.user_id == user_id,
                KnowledgeEdge.confidence >= min_confidence
            )
            .order_by(KnowledgeEdge.confidence.desc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_memory_edges(
        self,
        memory_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Sequence[KnowledgeEdge]:
        stmt = select(KnowledgeEdge).where(
            KnowledgeEdge.user_id == user_id,
            or_(
                KnowledgeEdge.source_memory_id == memory_id,
                KnowledgeEdge.target_memory_id == memory_id
            )
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_multi_node_edges(
        self,
        memory_ids: set[uuid.UUID],
        user_id: uuid.UUID
    ) -> Sequence[KnowledgeEdge]:
        if not memory_ids:
            return []
        stmt = select(KnowledgeEdge).where(
            KnowledgeEdge.user_id == user_id,
            or_(
                KnowledgeEdge.source_memory_id.in_(memory_ids),
                KnowledgeEdge.target_memory_id.in_(memory_ids)
            )
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()
