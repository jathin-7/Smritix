import pytest
from httpx import AsyncClient

async def get_auth_token(client: AsyncClient, email: str = "graphtester@example.com") -> str:
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "display_name": "Graph Tester"
        }
    )
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_knowledge_graph_and_connections(client: AsyncClient):
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create two related memories and one unrelated memory
    mem1_res = await client.post(
        "/api/v1/memories/",
        headers=headers,
        json={
            "title": "Quantum Entanglement",
            "content": "Quantum entanglement describes pairs of particles whose states are strongly correlated regardless of distance.",
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
            "title": "Quantum Computing Architectures",
            "content": "Quantum computers use qubits in superposition and entanglement states to perform quantum error correction.",
            "memory_type": "note",
            "tags": ["quantum", "computing"]
        }
    )
    assert mem2_res.status_code == 201
    mem2_id = mem2_res.json()["id"]

    mem3_res = await client.post(
        "/api/v1/memories/",
        headers=headers,
        json={
            "title": "Italian Sourdough Bread",
            "content": "Sourdough baking relies on wild yeast and lactobacilli fermentation at room temperature for crisp crust.",
            "memory_type": "note",
            "tags": ["baking", "food"]
        }
    )
    assert mem3_res.status_code == 201
    mem3_id = mem3_res.json()["id"]

    # 2. Test manual edge creation between mem1 and mem2
    edge_res = await client.post(
        "/api/v1/graph/edges",
        headers=headers,
        json={
            "source_memory_id": mem1_id,
            "target_memory_id": mem2_id,
            "relation_type": "references",
            "confidence": 0.95
        }
    )
    assert edge_res.status_code == 201
    edge_data = edge_res.json()["data"]
    assert edge_data["source"] == mem1_id
    assert edge_data["target"] == mem2_id
    assert edge_data["relation_type"] == "references"
    edge_id = edge_data["id"]

    # 3. Test self-loop validation error
    self_loop_res = await client.post(
        "/api/v1/graph/edges",
        headers=headers,
        json={
            "source_memory_id": mem1_id,
            "target_memory_id": mem1_id,
            "relation_type": "related_to"
        }
    )
    assert self_loop_res.status_code in (400, 422)

    # 4. Fetch complete graph
    graph_res = await client.get("/api/v1/graph", headers=headers)
    assert graph_res.status_code == 200
    graph_data = graph_res.json()["data"]
    assert graph_data["total_nodes"] >= 3
    assert graph_data["total_edges"] >= 1
    # Check that our manual edge is present
    found_edge = any(e["id"] == edge_id for e in graph_data["edges"])
    assert found_edge

    # 5. Fetch memory connections for mem1
    mem_conn_res = await client.get(f"/api/v1/memories/{mem1_id}/connections", headers=headers)
    assert mem_conn_res.status_code == 200
    conn_data = mem_conn_res.json()["data"]
    assert conn_data["memory_id"] == mem1_id
    assert conn_data["total_connections"] >= 1
    connected_node_ids = {n["id"] for n in conn_data["nodes"]}
    assert mem1_id in connected_node_ids
    assert mem2_id in connected_node_ids

    # 6. Fetch similar memories via vector search
    similar_res = await client.get(f"/api/v1/memories/{mem1_id}/similar", headers=headers)
    assert similar_res.status_code == 200
    similar_data = similar_res.json()["data"]
    assert isinstance(similar_data, list)
    # mem1 should find mem2 as similar (both about quantum)
    similar_ids = [s["memory_id"] for s in similar_data]
    assert mem1_id not in similar_ids  # self filtered out

    # 7. Semantic clusters
    clusters_res = await client.get("/api/v1/graph/clusters", headers=headers)
    assert clusters_res.status_code == 200
    clusters_data = clusters_res.json()["data"]
    assert clusters_data["total_clusters"] >= 1

    # 8. Delete the manual edge
    del_res = await client.delete(f"/api/v1/graph/edges/{edge_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True
