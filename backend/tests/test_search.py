import pytest
from httpx import AsyncClient

async def get_auth_token(client: AsyncClient, email: str = "searchtester@example.com") -> str:
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "display_name": "Search Tester"
        }
    )
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_search_and_history(client: AsyncClient):
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create memories on different topics
    await client.post(
        "/api/v1/memories/",
        headers=headers,
        json={
            "title": "Quantum Computing Principles",
            "content": "Quantum superposition and entanglement enable quantum computers to solve specific algorithms exponentially faster.",
            "memory_type": "note",
            "tags": ["physics", "quantum"]
        }
    )

    await client.post(
        "/api/v1/memories/",
        headers=headers,
        json={
            "title": "Python AsyncIO Guide",
            "content": "Asyncio uses an event loop to run cooperative multitasking tasks with async and await keywords.",
            "memory_type": "code",
            "tags": ["python", "async"]
        }
    )

    await client.post(
        "/api/v1/memories/",
        headers=headers,
        json={
            "title": "Homemade Neapolitan Pizza Recipe",
            "content": "Ferment pizza dough for 24 hours at room temperature, then bake in a 450 degree wood-fired oven.",
            "memory_type": "note",
            "tags": ["cooking", "food"]
        }
    )

    # 2. Semantic Search
    sem_res = await client.post(
        "/api/v1/search/",
        headers=headers,
        json={
            "query": "quantum entanglement physics",
            "limit": 5
        }
    )
    assert sem_res.status_code == 200, sem_res.text
    sem_data = sem_res.json()
    assert sem_data["search_type"] == "semantic"
    assert len(sem_data["results"]) > 0
    # Top result should be the quantum memory
    assert "Quantum" in sem_data["results"][0]["title"]

    # 3. Hybrid Search
    hybrid_res = await client.post(
        "/api/v1/search/hybrid",
        headers=headers,
        json={
            "query": "asyncio event loop python",
            "limit": 5
        }
    )
    assert hybrid_res.status_code == 200, hybrid_res.text
    hybrid_data = hybrid_res.json()
    assert hybrid_data["search_type"] == "hybrid"
    assert len(hybrid_data["results"]) > 0
    assert "AsyncIO" in hybrid_data["results"][0]["title"]

    # 4. Search with filters (memory_type)
    filtered_res = await client.post(
        "/api/v1/search/hybrid",
        headers=headers,
        json={
            "query": "pizza recipe",
            "memory_type": "note",
            "limit": 5
        }
    )
    assert filtered_res.status_code == 200
    assert any("Pizza" in r["title"] for r in filtered_res.json()["results"])

    # 5. Search History
    history_res = await client.get("/api/v1/search/history", headers=headers)
    assert history_res.status_code == 200
    history = history_res.json()["items"]
    assert len(history) >= 2
    queries = [h["query"] for h in history]
    assert "quantum entanglement physics" in queries
    assert "asyncio event loop python" in queries
