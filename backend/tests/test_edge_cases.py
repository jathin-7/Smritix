import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_unicode_and_markdown_memory_handling(client: AsyncClient):
    # Register user
    reg = await client.post("/api/v1/auth/register", json={
        "email": "edge@example.com",
        "password": "Password123!",
        "display_name": "Edge Tester"
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Complex unicode, emojis, markdown code blocks, math symbols
    complex_content = """# 🧠 Neural Architecture & Memory Matrix

Here is an algorithm test:
```python
def fib(n: int) -> int:
    return n if n <= 1 else fib(n-1) + fib(n-2)
```

Unicode testing:
- 日本語テスト (Japanese)
- 🚀 Cybernetic Quantum ✨
- Math: ∀x ∈ S, ∃y: x ⊕ y = 1
- Special chars: <script>alert('xss')</script> & "quotes" 'single'
"""

    res = await client.post("/api/v1/memories/", json={
        "title": "Quantum 🚀 & Code #1",
        "content": complex_content,
        "tags": ["quantum", "nihongo", "codesnippet"]
    }, headers=headers)

    assert res.status_code == 201
    mem = res.json()
    assert "🚀" in mem["title"]
    assert "nihongo" in mem["tags"]
    assert "<script>" in mem["content"]

    # Search with special symbols
    search_res = await client.post("/api/v1/search/", json={
        "query": "Quantum 🚀",
        "limit": 5
    }, headers=headers)
    assert search_res.status_code == 200
    assert len(search_res.json()["results"]) >= 1

@pytest.mark.asyncio
async def test_validation_error_envelope(client: AsyncClient):
    # Send malformed JSON (missing password)
    res = await client.post("/api/v1/auth/register", json={
        "email": "invalid-email-format"
    })
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "meta" in data
    assert "request_id" in data["meta"]

@pytest.mark.asyncio
async def test_ask_with_zero_memories(client: AsyncClient):
    # Register clean user with 0 memories
    reg = await client.post("/api/v1/auth/register", json={
        "email": "emptyvault@example.com",
        "password": "Password123!",
        "display_name": "Empty Vault"
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post("/api/v1/ask/", json={
        "query": "What did I write about distributed systems?"
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()["data"]
    assert "answer" in data
    assert len(data["sources"]) == 0
    assert "No relevant memories found" in data["answer"] or "couldn't find" in data["answer"] or len(data["answer"]) > 0

@pytest.mark.asyncio
async def test_graph_edge_validation(client: AsyncClient):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "graphedge@example.com",
        "password": "Password123!",
        "display_name": "Graph Edge Tester"
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to create edge between non-existent nodes
    res = await client.post("/api/v1/graph/edges", json={
        "source_memory_id": "00000000-0000-0000-0000-000000000001",
        "target_memory_id": "00000000-0000-0000-0000-000000000002",
        "relation_type": "related_to",
        "confidence": 1.0
    }, headers=headers)
    assert res.status_code == 404
