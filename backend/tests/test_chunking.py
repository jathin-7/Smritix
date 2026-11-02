import pytest
from app.pipelines.chunking import RecursiveCharacterChunker

def test_chunking_short_text():
    chunker = RecursiveCharacterChunker(chunk_size=500, chunk_overlap=50)
    text = "Short note about personal memory systems."
    chunks = chunker.split_text(text)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].content == text
    assert chunks[0].token_count > 0

def test_chunking_paragraphs():
    chunker = RecursiveCharacterChunker(chunk_size=100, chunk_overlap=20)
    p1 = "Paragraph 1 is about AI memory systems and architectural design."
    p2 = "Paragraph 2 discusses vector databases and dense embeddings for semantic search."
    p3 = "Paragraph 3 explains knowledge graph connections between memories."
    text = f"{p1}\n\n{p2}\n\n{p3}"

    chunks = chunker.split_text(text, metadata={"source": "test"})
    assert len(chunks) >= 3
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i
        assert chunk.metadata.get("source") == "test"
        assert len(chunk.content) > 0

def test_chunking_overlap():
    chunker = RecursiveCharacterChunker(chunk_size=80, chunk_overlap=30)
    text = (
        "The quick brown fox jumps over the lazy dog. "
        "Every good programmer knows that unit tests prevent regressions. "
        "Python and FastAPI provide great tools for asynchronous web APIs."
    )
    chunks = chunker.split_text(text)
    assert len(chunks) > 1
    # Check that chunk indices are sequential
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
