import pytest
import math
from app.ai.providers.local_fallback import LocalDeterministicEmbeddingProvider
from app.pipelines.embedding import EmbeddingPipeline
from app.pipelines.chunking import TextChunk

@pytest.mark.asyncio
async def test_deterministic_embedding_provider():
    provider = LocalDeterministicEmbeddingProvider(dimensions=384)
    assert provider.dimensions == 384

    texts = ["FastAPI is an async Python framework.", "Qdrant is a high performance vector database."]
    embeddings = await provider.embed(texts)

    assert len(embeddings) == 2
    for emb in embeddings:
        assert len(emb) == 384
        # Verify L2 normalization (sum of squares ~ 1.0)
        norm = math.sqrt(sum(v * v for v in emb))
        assert abs(norm - 1.0) < 1e-4

@pytest.mark.asyncio
async def test_embedding_pipeline():
    provider = LocalDeterministicEmbeddingProvider(dimensions=384)
    pipeline = EmbeddingPipeline(provider=provider, batch_size=2)

    chunks = [
        TextChunk(chunk_index=0, content="Chunk one text", token_count=3),
        TextChunk(chunk_index=1, content="Chunk two text", token_count=3),
        TextChunk(chunk_index=2, content="Chunk three text", token_count=3),
    ]

    embedded = await pipeline.process_chunks(chunks)
    assert len(embedded) == 3
    for i, ec in enumerate(embedded):
        assert ec.chunk.chunk_index == i
        assert len(ec.embedding) == 384
        assert ec.content_hash
        assert ec.embedding_id
