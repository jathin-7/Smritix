import pytest
from httpx import AsyncClient

async def get_auth_token(client: AsyncClient, email: str = "dashtester@example.com") -> str:
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "display_name": "Dashboard Tester"
        }
    )
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_dashboard_endpoints(client: AsyncClient):
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create memories with different types and tags
    mem1_res = await client.post(
        "/api/v1/memories/",
        headers=headers,
        json={
            "title": "Quantum Teleportation Notes",
            "content": "Quantum teleportation transfers quantum information using entangled states.",
            "memory_type": "note",
            "tags": ["quantum", "physics"]
        }
    )
    assert mem1_res.status_code == 201
    mem1_id = mem1_res.json()["id"]

    mem2_res = await client.post(
        "/api/v1/memories/",
        headers=headers,
        json={
            "title": "FastAPI Async Implementation",
            "content": "def run_app(): pass with asyncio event loop.",
            "memory_type": "code",
            "tags": ["python", "async"]
        }
    )
    assert mem2_res.status_code == 201
    mem2_id = mem2_res.json()["id"]

    # 2. Create knowledge edge
    await client.post(
        "/api/v1/graph/edges",
        headers=headers,
        json={
            "source_memory_id": mem1_id,
            "target_memory_id": mem2_id,
            "relation_type": "related_to"
        }
    )

    # 3. Test GET /api/v1/dashboard/stats
    stats_res = await client.get("/api/v1/dashboard/stats", headers=headers)
    assert stats_res.status_code == 200
    stats_data = stats_res.json()["data"]
    assert stats_data["total_memories"] >= 2
    assert stats_data["new_this_week"] >= 2
    assert stats_data["total_edges"] >= 1
    assert len(stats_data["types"]) >= 2
    assert len(stats_data["activity"]) == 7

    # 4. Test GET /api/v1/dashboard/timeline
    timeline_res = await client.get("/api/v1/dashboard/timeline", headers=headers)
    assert timeline_res.status_code == 200
    timeline_data = timeline_res.json()["data"]
    assert timeline_data["total"] >= 2
    assert len(timeline_data["groups"]) >= 1

    # 5. Test GET /api/v1/dashboard/knowledge-gaps
    gaps_res = await client.get("/api/v1/dashboard/knowledge-gaps", headers=headers)
    assert gaps_res.status_code == 200
    gaps_data = gaps_res.json()["data"]
    assert "health_score" in gaps_data
    assert gaps_data["health_score"] >= 0

    # 6. Test GET /api/v1/settings/ai and privacy
    ai_settings = await client.get("/api/v1/settings/ai", headers=headers)
    assert ai_settings.status_code == 200
    assert ai_settings.json()["data"]["local_only"] is True

    privacy_settings = await client.get("/api/v1/settings/privacy", headers=headers)
    assert privacy_settings.status_code == 200
    assert privacy_settings.json()["data"]["local_first"] is True
