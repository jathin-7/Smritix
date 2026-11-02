from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.models.memory import Memory, MemoryChunk, Tag, MemoryTag
from app.models.graph import KnowledgeEdge
from app.models.conversation import Conversation
from app.schemas.dashboard import (
    DashboardStatsResponse,
    TypeBreakdownItem,
    ActivityDayItem,
    TopTagItem,
    TimelineResponse,
    TimelineDayGroup,
    TimelineMemoryItem,
    KnowledgeGapsResponse,
    KnowledgeGapItem
)

TYPE_COLORS: dict[str, str] = {
  "note": "#10b981",
  "document": "#3b82f6",
  "code": "#8b5cf6",
  "snippet": "#a855f7",
  "conversation": "#f59e0b",
  "web_clip": "#06b6d4",
  "annotation": "#ec4899"
}

class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_stats(self, user_id: uuid.UUID) -> DashboardStatsResponse:
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        # 1. Total active memories
        mem_count_stmt = select(func.count(Memory.id)).where(
            Memory.user_id == user_id,
            Memory.is_deleted.is_(False)
        )
        total_memories = (await self.session.execute(mem_count_stmt)).scalar() or 0

        # 2. Memories created this week
        new_week_stmt = select(func.count(Memory.id)).where(
            Memory.user_id == user_id,
            Memory.is_deleted.is_(False),
            Memory.created_at >= week_ago
        )
        new_this_week = (await self.session.execute(new_week_stmt)).scalar() or 0

        # 3. Total knowledge graph edges
        edges_stmt = select(func.count(KnowledgeEdge.id)).where(
            KnowledgeEdge.user_id == user_id
        )
        total_edges = (await self.session.execute(edges_stmt)).scalar() or 0

        # 4. Total conversations
        conv_stmt = select(func.count(Conversation.id)).where(
            Conversation.user_id == user_id
        )
        total_conversations = (await self.session.execute(conv_stmt)).scalar() or 0

        # 5. Total chunks indexed
        chunks_stmt = (
            select(func.count(MemoryChunk.id))
            .join(Memory, Memory.id == MemoryChunk.memory_id)
            .where(
                Memory.user_id == user_id,
                Memory.is_deleted.is_(False)
            )
        )
        total_chunks = (await self.session.execute(chunks_stmt)).scalar() or 0

        # 6. Memory type breakdown
        type_stmt = (
            select(Memory.memory_type, func.count(Memory.id))
            .where(Memory.user_id == user_id, Memory.is_deleted.is_(False))
            .group_by(Memory.memory_type)
        )
        type_rows = (await self.session.execute(type_stmt)).all()
        types: list[TypeBreakdownItem] = []
        for m_type, count in type_rows:
            pct = round((count / total_memories) * 100, 1) if total_memories > 0 else 0.0
            types.append(
                TypeBreakdownItem(
                    memory_type=m_type,
                    count=count,
                    percentage=pct,
                    color=TYPE_COLORS.get(m_type, "#64748b")
                )
            )

        # 7. 7-Day Activity Sparkline
        activity_map: dict[str, int] = defaultdict(int)
        act_stmt = (
            select(Memory.created_at)
            .where(
                Memory.user_id == user_id,
                Memory.is_deleted.is_(False),
                Memory.created_at >= week_ago
            )
        )
        act_rows = (await self.session.execute(act_stmt)).scalars().all()
        for dt in act_rows:
            date_str = dt.strftime("%Y-%m-%d")
            activity_map[date_str] += 1

        activity_items: list[ActivityDayItem] = []
        for d in range(6, -1, -1):
            day_dt = now - timedelta(days=d)
            date_key = day_dt.strftime("%Y-%m-%d")
            day_name = day_dt.strftime("%a")
            activity_items.append(
                ActivityDayItem(
                    date=date_key,
                    day_name=day_name,
                    count=activity_map[date_key]
                )
            )

        # 8. Top Tags
        top_tags: list[TopTagItem] = []
        try:
            tags_stmt = (
                select(Tag.name, func.count(MemoryTag.c.memory_id))
                .join(MemoryTag, Tag.id == MemoryTag.c.tag_id)
                .where(Tag.user_id == user_id)
                .group_by(Tag.name)
                .order_by(func.count(MemoryTag.c.memory_id).desc())
                .limit(6)
            )
            tag_rows = (await self.session.execute(tags_stmt)).all()
            for t_name, count in tag_rows:
                top_tags.append(TopTagItem(name=t_name, count=count))
        except Exception:
            pass

        return DashboardStatsResponse(
            total_memories=total_memories,
            new_this_week=new_this_week,
            total_edges=total_edges,
            total_conversations=total_conversations,
            total_chunks=total_chunks,
            types=types,
            activity=activity_items,
            top_tags=top_tags
        )

    async def get_timeline(self, user_id: uuid.UUID, limit: int = 50) -> TimelineResponse:
        stmt = (
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.is_deleted.is_(False)
            )
            .options(selectinload(Memory.tags))
            .order_by(Memory.created_at.desc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        memories = res.scalars().unique().all()

        day_map: dict[str, list[TimelineMemoryItem]] = defaultdict(list)
        for m in memories:
            date_key = m.created_at.strftime("%Y-%m-%d")
            tag_names = [t.name for t in m.tags] if m.tags else []
            day_map[date_key].append(
                TimelineMemoryItem(
                    id=m.id,
                    title=m.title or "Untitled Memory",
                    snippet=m.content[:150],
                    memory_type=m.memory_type,
                    tags=tag_names,
                    created_at=m.created_at
                )
            )

        groups: list[TimelineDayGroup] = []
        for date_key, items in day_map.items():
            dt = datetime.strptime(date_key, "%Y-%m-%d")
            formatted = dt.strftime("%B %d, %Y")
            groups.append(
                TimelineDayGroup(
                    date=date_key,
                    formatted_date=formatted,
                    memories=items
                )
            )

        return TimelineResponse(groups=groups, total=len(memories))

    async def get_knowledge_gaps(self, user_id: uuid.UUID) -> KnowledgeGapsResponse:
        # Load active memories
        stmt = (
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.is_deleted.is_(False)
            )
            .options(selectinload(Memory.tags))
        )
        res = await self.session.execute(stmt)
        memories = res.scalars().unique().all()

        if not memories:
            return KnowledgeGapsResponse(
                gaps=[],
                orphaned_count=0,
                untagged_count=0,
                health_score=100
            )

        # Get connected memory IDs
        edge_stmt = select(KnowledgeEdge.source_memory_id, KnowledgeEdge.target_memory_id).where(
            KnowledgeEdge.user_id == user_id
        )
        edge_rows = (await self.session.execute(edge_stmt)).all()
        connected_ids: set[uuid.UUID] = set()
        for src, tgt in edge_rows:
            connected_ids.add(src)
            connected_ids.add(tgt)

        gaps: list[KnowledgeGapItem] = []
        orphaned_count = 0
        untagged_count = 0

        for m in memories:
            is_orphaned = m.id not in connected_ids
            is_untagged = not m.tags or len(m.tags) == 0

            if is_orphaned:
                orphaned_count += 1
                gaps.append(
                    KnowledgeGapItem(
                        memory_id=m.id,
                        title=m.title or "Untitled Memory",
                        memory_type=m.memory_type,
                        reason="No connections in the knowledge graph"
                    )
                )
            elif is_untagged:
                untagged_count += 1
                gaps.append(
                    KnowledgeGapItem(
                        memory_id=m.id,
                        title=m.title or "Untitled Memory",
                        memory_type=m.memory_type,
                        reason="Missing tags or topic categories"
                    )
                )

        total_count = len(memories)
        orphaned_penalty = (orphaned_count / total_count) * 45
        untagged_penalty = (untagged_count / total_count) * 25
        health_score = max(10, min(100, int(100 - orphaned_penalty - untagged_penalty)))

        return KnowledgeGapsResponse(
            gaps=gaps[:12],
            orphaned_count=orphaned_count,
            untagged_count=untagged_count,
            health_score=health_score
        )
