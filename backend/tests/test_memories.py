import pytest
from httpx import AsyncClient

async def get_auth_token(client: AsyncClient, email: str = "memtest@example.com") -> str:
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "display_name": "Memory Tester"
        }
    )
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_memory_crud(client: AsyncClient):
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a memory
    create_res = await client.post(
        "/api/v1/memories/",
        headers=headers,
        json={
            "title": "Architecture Overview",
            "content": "SMRITIX is designed as a local-first personal AI memory system.",
            "memory_type": "note",
            "tags": ["architecture", "smritix"]
        }
    )
    assert create_res.status_code == 201, create_res.text
    mem_data = create_res.json()
    memory_id = mem_data["id"]
    assert mem_data["title"] == "Architecture Overview"
    assert "architecture" in mem_data["tags"]
    assert "smritix" in mem_data["tags"]

    # 2. Get memory detail
    get_res = await client.get(f"/api/v1/memories/{memory_id}", headers=headers)
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["id"] == memory_id
    assert len(detail["chunks"]) > 0

    # 3. Update memory
    patch_res = await client.patch(
        f"/api/v1/memories/{memory_id}",
        headers=headers,
        json={
            "title": "Architecture Overview Updated",
            "tags": ["architecture", "v1"]
        }
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["title"] == "Architecture Overview Updated"
    assert "v1" in updated["tags"]
    assert "smritix" not in updated["tags"]

    # 4. List memories
    list_res = await client.get("/api/v1/memories/", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(m["id"] == memory_id for m in list_data["items"])

    # 5. Filter list by tag
    tag_list_res = await client.get("/api/v1/memories/?tag=v1", headers=headers)
    assert tag_list_res.status_code == 200
    assert tag_list_res.json()["total"] >= 1

    # 6. Filter list by query
    query_res = await client.get("/api/v1/memories/?query=Architecture", headers=headers)
    assert query_res.status_code == 200
    assert query_res.json()["total"] >= 1

    # 7. Archive memory
    archive_res = await client.post(f"/api/v1/memories/{memory_id}/archive", headers=headers)
    assert archive_res.status_code == 200
    assert archive_res.json()["is_archived"] is True

    # 8. Restore memory
    restore_res = await client.post(f"/api/v1/memories/{memory_id}/restore", headers=headers)
    assert restore_res.status_code == 200
    assert restore_res.json()["is_archived"] is False

    # 9. Delete memory (soft delete)
    del_res = await client.delete(f"/api/v1/memories/{memory_id}", headers=headers)
    assert del_res.status_code == 204

    # 10. Verify deleted memory is no longer found
    not_found_res = await client.get(f"/api/v1/memories/{memory_id}", headers=headers)
    assert not_found_res.status_code == 404
