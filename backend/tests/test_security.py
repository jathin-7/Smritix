import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    res = await client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "healthy"
    assert data["architecture"] == "local-first"
    assert "X-Request-ID" in res.headers

@pytest.mark.asyncio
async def test_unauthorized_endpoints(client: AsyncClient):
    # Without authorization header
    res1 = await client.get("/api/v1/memories/")
    assert res1.status_code == 401

    res2 = await client.post("/api/v1/memories/", json={"content": "secret"})
    assert res2.status_code == 401

    res3 = await client.get("/api/v1/dashboard/stats")
    assert res3.status_code == 401

    res4 = await client.get("/api/v1/graph/")
    assert res4.status_code == 401

    # With invalid/tampered token
    invalid_headers = {"Authorization": "Bearer invalid.jwt.token"}
    res5 = await client.get("/api/v1/memories/", headers=invalid_headers)
    assert res5.status_code == 401

@pytest.mark.asyncio
async def test_multitenant_memory_isolation(client: AsyncClient):
    # Register User A
    res_a = await client.post("/api/v1/auth/register", json={
        "email": "usera@example.com",
        "password": "Password123!",
        "display_name": "User A"
    })
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register User B
    res_b = await client.post("/api/v1/auth/register", json={
        "email": "userb@example.com",
        "password": "Password123!",
        "display_name": "User B"
    })
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a confidential memory
    res_mem_a = await client.post("/api/v1/memories/", json={
        "title": "User A Private Note",
        "content": "This contains highly confidential thoughts for User A.",
        "tags": ["confidential"]
    }, headers=headers_a)
    assert res_mem_a.status_code == 201
    mem_a_id = res_mem_a.json()["id"]

    # User B attempts to read User A's memory -> 404 Not Found (isolated)
    res_get_b = await client.get(f"/api/v1/memories/{mem_a_id}", headers=headers_b)
    assert res_get_b.status_code == 404

    # User B attempts to update User A's memory -> 404
    res_update_b = await client.patch(f"/api/v1/memories/{mem_a_id}", json={
        "title": "Hacked Note"
    }, headers=headers_b)
    assert res_update_b.status_code == 404

    # User B attempts to delete User A's memory -> 404
    res_del_b = await client.delete(f"/api/v1/memories/{mem_a_id}", headers=headers_b)
    assert res_del_b.status_code == 404

    # User B lists memories -> should be 0 items
    res_list_b = await client.get("/api/v1/memories/", headers=headers_b)
    assert res_list_b.json()["total"] == 0

    # User A lists memories -> should be 1 item
    res_list_a = await client.get("/api/v1/memories/", headers=headers_a)
    assert res_list_a.json()["total"] == 1

@pytest.mark.asyncio
async def test_multitenant_conversation_isolation(client: AsyncClient):
    # Register User 1
    res1 = await client.post("/api/v1/auth/register", json={
        "email": "userone@example.com",
        "password": "Password123!",
        "display_name": "User 1"
    })
    assert res1.status_code == 201
    token1 = res1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Register User 2
    res2 = await client.post("/api/v1/auth/register", json={
        "email": "usertwo@example.com",
        "password": "Password123!",
        "display_name": "User 2"
    })
    assert res2.status_code == 201
    token2 = res2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 1 starts a conversation
    ask_res1 = await client.post("/api/v1/ask/", json={
        "query": "What is quantum computing?"
    }, headers=headers1)
    assert ask_res1.status_code == 200
    conv_id1 = ask_res1.json()["data"]["conversation_id"]

    # User 2 tries to read User 1's conversation -> 404
    res_conv_b = await client.get(f"/api/v1/ask/conversations/{conv_id1}", headers=headers2)
    assert res_conv_b.status_code == 404

    # User 2 lists conversations -> should be empty
    res_convs_b = await client.get("/api/v1/ask/conversations", headers=headers2)
    assert len(res_convs_b.json()["data"]) == 0
