from __future__ import annotations
import uuid
import hashlib
from dataclasses import dataclass
from app.ai.interfaces import EmbeddingProvider
from app.pipelines.chunking import TextChunk

@dataclass
class EmbeddedChunk:
    chunk: TextChunk
    embedding: list[float]
    embedding_id: str
    content_hash: str

class EmbeddingPipeline:
    def __init__(self, provider: EmbeddingProvider, batch_size: int = 16):
        self.provider = provider
        self.batch_size = batch_size

    @staticmethod
    def compute_hash(text: str) -> str:
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    async def process_chunks(self, chunks: list[TextChunk]) -> list[EmbeddedChunk]:
        if not chunks:
            return []

        results: list[EmbeddedChunk] = []

        # Process in batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            texts = [c.content for c in batch]
            embeddings = await self.provider.embed(texts)

            for chunk, emb in zip(batch, embeddings):
                content_hash = self.compute_hash(chunk.content)
                emb_id = str(uuid.uuid4())
                results.append(
                    EmbeddedChunk(
                        chunk=chunk,
                        embedding=emb,
                        embedding_id=emb_id,
                        content_hash=content_hash
                    )
                )
        return results
