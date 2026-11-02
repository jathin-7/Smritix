from __future__ import annotations
import uuid
from typing import Sequence, Any
from collections import defaultdict, deque
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph import KnowledgeEdge
from app.models.memory import Memory, Tag
from app.repositories.graph_repository import GraphRepository
from app.repositories.memory_repository import MemoryRepository
from app.services.search_service import SearchService
from app.schemas.graph import (
    GraphNodeItem,
    GraphEdgeItem,
    GraphResponse,
    CreateEdgeRequest,
    ClusterItem,
    ClustersResponse,
    MemoryConnectionsResponse
)
from app.core.exceptions import NotFoundError, ValidationError

class GraphService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.graph_repo = GraphRepository(session)
        self.memory_repo = MemoryRepository(session)
        self.search_service = SearchService(session)

    async def create_edge(
        self,
        user_id: uuid.UUID,
        data: CreateEdgeRequest,
        created_by: str = "user"
    ) -> GraphEdgeItem:
        if data.source_memory_id == data.target_memory_id:
            raise ValidationError("Source and target memory cannot be identical")

        # Verify source memory exists
        source_mem = await self.memory_repo.get_by_id_and_user(data.source_memory_id, user_id)
        if not source_mem or source_mem.is_deleted:
            raise NotFoundError("Source memory not found")

        # Verify target memory exists
        target_mem = await self.memory_repo.get_by_id_and_user(data.target_memory_id, user_id)
        if not target_mem or target_mem.is_deleted:
            raise NotFoundError("Target memory not found")

        edge = await self.graph_repo.create_or_update_edge(
            user_id=user_id,
            source_memory_id=data.source_memory_id,
            target_memory_id=data.target_memory_id,
            relation_type=data.relation_type,
            confidence=data.confidence,
            created_by=created_by,
            metadata=data.metadata
        )
        await self.session.commit()

        return GraphEdgeItem(
            id=edge.id,
            source=edge.source_memory_id,
            target=edge.target_memory_id,
            relation_type=edge.relation_type,
            confidence=edge.confidence,
            created_by=edge.created_by,
            metadata=edge.metadata_,
            created_at=edge.created_at
        )

    async def delete_edge(self, edge_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        deleted = await self.graph_repo.delete_edge(edge_id, user_id)
        if deleted:
            await self.session.commit()
        return deleted

    async def get_graph(
        self,
        user_id: uuid.UUID,
        tag: str | None = None,
        memory_type: str | None = None,
        limit: int = 150
    ) -> GraphResponse:
        # Load active memories for user
        stmt = (
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.is_deleted.is_(False),
                Memory.is_archived.is_(False)
            )
            .options(selectinload(Memory.tags))
            .order_by(Memory.updated_at.desc())
        )
        if memory_type:
            stmt = stmt.where(Memory.memory_type == memory_type)
        if tag:
            stmt = stmt.join(Memory.tags).where(Tag.name == tag.strip())

        res = await self.session.execute(stmt.limit(limit))
        memories = res.scalars().unique().all()
        memory_ids = {m.id for m in memories}

        if not memory_ids:
            return GraphResponse(nodes=[], edges=[], total_nodes=0, total_edges=0)

        # Load edges for user
        edges_raw = await self.graph_repo.get_user_edges(user_id=user_id, limit=500)

        # Filter edges where both endpoints are in active memory set
        valid_edges: list[GraphEdgeItem] = []
        connection_counts: dict[uuid.UUID, int] = defaultdict(int)

        for e in edges_raw:
            if e.source_memory_id in memory_ids and e.target_memory_id in memory_ids:
                valid_edges.append(
                    GraphEdgeItem(
                        id=e.id,
                        source=e.source_memory_id,
                        target=e.target_memory_id,
                        relation_type=e.relation_type,
                        confidence=round(e.confidence, 3),
                        created_by=e.created_by,
                        metadata=e.metadata_,
                        created_at=e.created_at
                    )
                )
                connection_counts[e.source_memory_id] += 1
                connection_counts[e.target_memory_id] += 1

        node_items: list[GraphNodeItem] = []
        for m in memories:
            tags = [t.name for t in m.tags] if m.tags else []
            node_items.append(
                GraphNodeItem(
                    id=m.id,
                    title=m.title or "Untitled Memory",
                    snippet=m.content[:160],
                    memory_type=m.memory_type,
                    tags=tags,
                    connection_count=connection_counts[m.id],
                    created_at=m.created_at
                )
            )

        return GraphResponse(
            nodes=node_items,
            edges=valid_edges,
            total_nodes=len(node_items),
            total_edges=len(valid_edges)
        )

    async def get_node_connections(
        self,
        memory_id: uuid.UUID,
        user_id: uuid.UUID,
        depth: int = 1
    ) -> MemoryConnectionsResponse:
        # Verify base memory
        base_mem = await self.memory_repo.get_by_id_and_user(memory_id, user_id)
        if not base_mem or base_mem.is_deleted:
            raise NotFoundError("Memory not found")

        collected_node_ids: set[uuid.UUID] = {memory_id}
        current_frontier: set[uuid.UUID] = {memory_id}

        collected_edges: list[KnowledgeEdge] = []
        seen_edge_ids: set[uuid.UUID] = set()

        depth_limit = max(1, min(depth, 3))
        for _ in range(depth_limit):
            if not current_frontier:
                break
            edges = await self.graph_repo.get_multi_node_edges(current_frontier, user_id)
            next_frontier: set[uuid.UUID] = set()
            for e in edges:
                if e.id not in seen_edge_ids:
                    seen_edge_ids.add(e.id)
                    collected_edges.append(e)
                    for nid in (e.source_memory_id, e.target_memory_id):
                        if nid not in collected_node_ids:
                            collected_node_ids.add(nid)
                            next_frontier.add(nid)
            current_frontier = next_frontier

        # Load all involved memories
        stmt = (
            select(Memory)
            .where(Memory.id.in_(collected_node_ids), Memory.is_deleted.is_(False))
            .options(selectinload(Memory.tags))
        )
        res = await self.session.execute(stmt)
        memories = res.scalars().unique().all()
        mem_map = {m.id: m for m in memories}

        connection_counts: dict[uuid.UUID, int] = defaultdict(int)
        edge_items: list[GraphEdgeItem] = []
        for e in collected_edges:
            if e.source_memory_id in mem_map and e.target_memory_id in mem_map:
                edge_items.append(
                    GraphEdgeItem(
                        id=e.id,
                        source=e.source_memory_id,
                        target=e.target_memory_id,
                        relation_type=e.relation_type,
                        confidence=round(e.confidence, 3),
                        created_by=e.created_by,
                        metadata=e.metadata_,
                        created_at=e.created_at
                    )
                )
                connection_counts[e.source_memory_id] += 1
                connection_counts[e.target_memory_id] += 1

        node_items: list[GraphNodeItem] = []
        for m in memories:
            tags = [t.name for t in m.tags] if m.tags else []
            node_items.append(
                GraphNodeItem(
                    id=m.id,
                    title=m.title or "Untitled Memory",
                    snippet=m.content[:160],
                    memory_type=m.memory_type,
                    tags=tags,
                    connection_count=connection_counts[m.id],
                    created_at=m.created_at
                )
            )

        return MemoryConnectionsResponse(
            memory_id=memory_id,
            nodes=node_items,
            edges=edge_items,
            total_connections=len(edge_items)
        )

    async def get_clusters(self, user_id: uuid.UUID) -> ClustersResponse:
        # Load user graph
        graph_data = await self.get_graph(user_id=user_id, limit=200)
        nodes = graph_data.nodes
        edges = graph_data.edges

        if not nodes:
            return ClustersResponse(clusters=[], total_clusters=0)

        # Adjacency map
        adj: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)
        for e in edges:
            adj[e.source].add(e.target)
            adj[e.target].add(e.source)

        visited: set[uuid.UUID] = set()
        clusters: list[ClusterItem] = []
        cluster_idx = 1

        node_map = {n.id: n for n in nodes}

        # Find connected components with BFS
        for n in nodes:
            if n.id in visited:
                continue

            component_ids: list[uuid.UUID] = []
            queue = deque([n.id])
            visited.add(n.id)

            while queue:
                curr = queue.popleft()
                component_ids.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited and neighbor in node_map:
                        visited.add(neighbor)
                        queue.append(neighbor)

            # Determine cluster label and tag summary
            all_tags: list[str] = []
            for nid in component_ids:
                all_tags.extend(node_map[nid].tags)

            tag_counts = defaultdict(int)
            for t in all_tags:
                tag_counts[t] += 1

            sorted_tags = sorted(tag_counts.keys(), key=lambda t: tag_counts[t], reverse=True)
            top_tags = sorted_tags[:3]

            # Choose prominent name
            if top_tags:
                cluster_name = f"{top_tags[0].capitalize()} Topic"
            else:
                # Use title of the highest connection node in this component
                best_node = max(component_ids, key=lambda nid: node_map[nid].connection_count)
                cluster_name = node_map[best_node].title[:30]

            clusters.append(
                ClusterItem(
                    id=f"cluster_{cluster_idx}",
                    name=cluster_name,
                    node_ids=component_ids,
                    size=len(component_ids),
                    tags=top_tags,
                    description=f"Group of {len(component_ids)} related memories"
                )
            )
            cluster_idx += 1

        # Sort clusters by size descending
        clusters.sort(key=lambda c: c.size, reverse=True)
        return ClustersResponse(clusters=clusters, total_clusters=len(clusters))

    async def discover_and_create_connections(
        self,
        user_id: uuid.UUID,
        memory_id: uuid.UUID,
        threshold: float = 0.65
    ) -> list[KnowledgeEdge]:
        """
        Auto-connection discovery:
        Finds semantically similar memories and forms 'similar_to' edges.
        """
        memory = await self.memory_repo.get_by_id_and_user(memory_id, user_id)
        if not memory or not memory.content:
            return []

        # Find candidates using semantic search
        candidates = await self.search_service.semantic_search(
            user_id=user_id,
            query=memory.content,
            limit=6,
            min_score=threshold
        )

        created_edges: list[KnowledgeEdge] = []
        for cand in candidates:
            if cand.memory_id == memory_id:
                continue

            edge = await self.graph_repo.create_or_update_edge(
                user_id=user_id,
                source_memory_id=memory_id,
                target_memory_id=cand.memory_id,
                relation_type="similar_to",
                confidence=round(cand.score, 3),
                created_by="ai",
                metadata={"cosine_similarity": cand.score, "auto_discovered": True}
            )
            created_edges.append(edge)

        if created_edges:
            await self.session.commit()

        return created_edges
