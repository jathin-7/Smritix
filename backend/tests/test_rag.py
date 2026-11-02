import pytest
import json
from httpx import AsyncClient

async def get_auth_token(client: AsyncClient, email: str = "ragtester@example.com") -> str:
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "display_name": "RAG Tester"
        }
    )
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_rag_pipeline_and_conversations(client: AsyncClient):
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Seed memories
    mem1_res = await client.post(
        "/api/v1/memories/",
        headers=headers,
        json={
            "title": "FastAPI Validation Architecture",
            "content": "FastAPI uses Pydantic models for data validation and automatic schema generation.",
            "memory_type": "note",
            "tags": ["fastapi", "python"]
        }
    )
    assert mem1_res.status_code == 201
    mem1_id = mem1_res.json()["id"]

    mem2_res = await client.post(
        "/api/v1/memories/",
        headers=headers,
        json={
            "title": "Database Engine Choice",
            "content": "SMRITIX uses PostgreSQL with SQLAlchemy 2.0 async engine and Alembic migrations for relational storage.",
            "memory_type": "note",
            "tags": ["database", "postgres"]
        }
    )
    assert mem2_res.status_code == 201

    # 2. Ask non-streaming question
    ask_res = await client.post(
        "/api/v1/ask/",
        headers=headers,
        json={
            "query": "What does FastAPI use for data validation?"
        }
    )
    assert ask_res.status_code == 200
    ask_data = ask_res.json()["data"]
    assert "conversation_id" in ask_data
    assert len(ask_data["sources"]) > 0
    assert "Pydantic" in ask_data["answer"]
    conv_id = ask_data["conversation_id"]

    # Verify source attribution
    source_ids = [s["memory_id"] for s in ask_data["sources"]]
    assert mem1_id in source_ids

    # 3. Ask follow-up question continuing the same conversation
    followup_res = await client.post(
        "/api/v1/ask/",
        headers=headers,
        json={
            "query": "Which database engine does SMRITIX use?",
            "conversation_id": conv_id
        }
    )
    assert followup_res.status_code == 200
    followup_data = followup_res.json()["data"]
    assert followup_data["conversation_id"] == conv_id
    assert "PostgreSQL" in followup_data["answer"]

    # 4. Test streaming endpoint (SSE)
    stream_res = await client.post(
        "/api/v1/ask/stream",
        headers=headers,
        json={
            "query": "What validation library is used?",
            "conversation_id": conv_id
        }
    )
    assert stream_res.status_code == 200
    assert "text/event-stream" in stream_res.headers["content-type"]

    lines = stream_res.text.strip().split("\n")
    events = [l for l in lines if l.startswith("data: ")]
    assert len(events) >= 2

    # Parse metadata event
    first_event = json.loads(events[0].replace("data: ", ""))
    assert first_event["type"] == "metadata"
    assert "sources" in first_event

    # Parse done event
    last_event = json.loads(events[-1].replace("data: ", ""))
    assert last_event["type"] == "done"

    # 5. List conversations
    convs_res = await client.get("/api/v1/ask/conversations", headers=headers)
    assert convs_res.status_code == 200
    conv_list = convs_res.json()["data"]
    assert len(conv_list) >= 1
    target_conv = next(c for c in conv_list if c["id"] == conv_id)
    # 3 user messages + 3 assistant messages = 6 messages
    assert target_conv["message_count"] >= 6

    # 6. Get conversation detail with resolved message history & sources
    detail_res = await client.get(f"/api/v1/ask/conversations/{conv_id}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()["data"]
    assert detail_data["id"] == conv_id
    assert len(detail_data["messages"]) >= 6

    # 7. Delete conversation
    del_res = await client.delete(f"/api/v1/ask/conversations/{conv_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify 404 after delete
    detail_res_after = await client.get(f"/api/v1/ask/conversations/{conv_id}", headers=headers)
    assert detail_res_after.status_code == 404
