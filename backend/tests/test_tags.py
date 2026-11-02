import pytest
from httpx import AsyncClient

async def get_auth_token(client: AsyncClient, email: str = "tagtest@example.com") -> str:
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "display_name": "Tag Tester"
        }
    )
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_tag_crud(client: AsyncClient):
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a tag
    create_res = await client.post(
        "/api/v1/tags/",
        headers=headers,
        json={"name": "ai-research", "color": "#3B82F6"}
    )
    assert create_res.status_code == 201, create_res.text
    tag = create_res.json()
    tag_id = tag["id"]
    assert tag["name"] == "ai-research"
    assert tag["color"] == "#3B82F6"

    # 2. List tags
    list_res = await client.get("/api/v1/tags/", headers=headers)
    assert list_res.status_code == 200
    tags = list_res.json()
    assert any(t["id"] == tag_id for t in tags)

    # 3. Update tag
    patch_res = await client.patch(
        f"/api/v1/tags/{tag_id}",
        headers=headers,
        json={"name": "deep-learning", "color": "#10B981"}
    )
    assert patch_res.status_code == 200
    updated_tag = patch_res.json()
    assert updated_tag["name"] == "deep-learning"
    assert updated_tag["color"] == "#10B981"

    # 4. Delete tag
    del_res = await client.delete(f"/api/v1/tags/{tag_id}", headers=headers)
    assert del_res.status_code == 204

    # 5. Verify tag no longer in list
    list_after = await client.get("/api/v1/tags/", headers=headers)
    assert not any(t["id"] == tag_id for t in list_after.json())
