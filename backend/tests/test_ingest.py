import io
import pytest
from httpx import AsyncClient

async def get_auth_token(client: AsyncClient, email: str = "ingestuser@example.com") -> str:
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "display_name": "Ingest Tester"
        }
    )
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_document_ingestion_api(client: AsyncClient):
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload Markdown document
    file_content = b"# Architecture Design\n\nThis document describes SMRITIX Phase 2 ingestion pipelines."
    files = {"file": ("architecture.md", io.BytesIO(file_content), "text/markdown")}
    data = {"tags": "architecture, phase2, design"}

    upload_res = await client.post(
        "/api/v1/ingest/document",
        headers=headers,
        files=files,
        data=data
    )
    assert upload_res.status_code == 202, upload_res.text
    job_data = upload_res.json()
    job_id = job_data["id"]
    assert job_data["status"] == "pending"
    assert job_data["source_uri"] == "architecture.md"

    # 2. Get Job Details
    job_res = await client.get(f"/api/v1/ingest/jobs/{job_id}", headers=headers)
    assert job_res.status_code == 200
    assert job_res.json()["id"] == job_id

    # 3. List Jobs
    list_res = await client.get("/api/v1/ingest/jobs", headers=headers)
    assert list_res.status_code == 200
    jobs = list_res.json()["items"]
    assert any(j["id"] == job_id for j in jobs)

    # 4. Unsupported file extension rejected with 400
    bad_files = {"file": ("bad_file.exe", io.BytesIO(b"executable"), "application/octet-stream")}
    bad_res = await client.post("/api/v1/ingest/document", headers=headers, files=bad_files)
    assert bad_res.status_code == 400
