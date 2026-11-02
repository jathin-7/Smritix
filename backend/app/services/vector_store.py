from __future__ import annotations
import uuid
from typing import Any
import httpx
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels
from app.config import get_settings

settings = get_settings()

class VectorStoreService:
    def __init__(self, url: str | None = None, collection_name: str | None = None):
        self.url = (url or settings.QDRANT_URL).rstrip("/")
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self._client: AsyncQdrantClient | None = None

    def _get_client(self) -> AsyncQdrantClient:
        if self._client is None:
            self._client = AsyncQdrantClient(url=self.url, timeout=5.0)
        return self._client

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                res = await client.get(f"{self.url}/healthz")
                return res.status_code == 200
        except Exception:
            return False

    async def ensure_collection(self, dimensions: int) -> bool:
        if not await self.is_available():
            return False

        client = self._get_client()
        try:
            collections = await client.get_collections()
            existing_names = [c.name for c in collections.collections]
            if self.collection_name not in existing_names:
                await client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=dimensions,
                        distance=qmodels.Distance.COSINE
                    )
                )
            return True
        except Exception:
            return False

    async def upsert_points(self, points: list[dict[str, Any]]) -> bool:
        """
        Expects points with structure:
        { "id": str, "vector": list[float], "payload": { "memory_id": str, "user_id": str, ... } }
        """
        if not points or not await self.is_available():
            return False

        client = self._get_client()
        try:
            q_points = [
                qmodels.PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p.get("payload", {})
                )
                for p in points
            ]
            await client.upsert(
                collection_name=self.collection_name,
                points=q_points
            )
            return True
        except Exception:
            return False

    async def search(
        self,
        query_vector: list[float],
        user_id: uuid.UUID,
        limit: int = 10,
        memory_type: str | None = None
    ) -> list[dict[str, Any]]:
        if not await self.is_available():
            return []

        client = self._get_client()
        try:
            # Filter by user_id for multi-tenant isolation
            must_conditions: list[Any] = [
                qmodels.FieldCondition(
                    key="user_id",
                    match=qmodels.MatchValue(value=str(user_id))
                )
            ]
            if memory_type:
                must_conditions.append(
                    qmodels.FieldCondition(
                        key="memory_type",
                        match=qmodels.MatchValue(value=memory_type)
                    )
                )

            filter_condition = qmodels.Filter(must=must_conditions)

            # Search in Qdrant
            hits = await client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=filter_condition,
                limit=limit,
                with_payload=True
            )

            results = []
            for hit in hits:
                payload = hit.payload or {}
                results.append({
                    "id": str(hit.id),
                    "score": float(hit.score),
                    "memory_id": payload.get("memory_id"),
                    "chunk_index": payload.get("chunk_index"),
                    "content": payload.get("content", ""),
                    "title": payload.get("title"),
                    "memory_type": payload.get("memory_type", "note"),
                    "tags": payload.get("tags", []),
                })
            return results
        except Exception:
            return []
