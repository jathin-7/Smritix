import os
import tempfile
import pytest
from pathlib import Path
from httpx import AsyncClient

from app.services.file_intelligence.extractor import FileExtractionService
from app.services.file_intelligence.chunker import FileChunkingService

async def get_auth_token(client: AsyncClient, email: str = "filetester@example.com") -> str:
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "display_name": "File Tester"
        }
    )
    if res.status_code == 201:
        return res.json()["access_token"]
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"}
    )
    return login_res.json()["access_token"]

def test_file_extraction_markdown_and_text():
    with tempfile.TemporaryDirectory() as tmpdir:
        md_file = Path(tmpdir) / "notes.md"
        md_file.write_text("# SMRITIX Architecture\n\nLocal-first sovereign memory system.\n\n## Security\nZero cloud egress.", encoding="utf-8")

        doc = FileExtractionService.extract(md_file)
        assert doc.title == "SMRITIX Architecture"
        assert "Local-first sovereign memory system" in doc.content
        assert len(doc.sections) >= 1

        txt_file = Path(tmpdir) / "code_sample.py"
        txt_file.write_text("def hello_world():\n    return 'Hello SMRITIX'", encoding="utf-8")
        doc_code = FileExtractionService.extract(txt_file)
        assert "hello_world" in doc_code.content

def test_file_chunking_with_sections():
    with tempfile.TemporaryDirectory() as tmpdir:
        md_file = Path(tmpdir) / "doc.md"
        md_file.write_text("# Chapter 1\n\n" + "Long text paragraph. " * 30 + "\n\n# Chapter 2\n\nSecond section content.", encoding="utf-8")

        doc = FileExtractionService.extract(md_file)
        chunker = FileChunkingService(target_chunk_size=300, overlap=50)
        chunks = chunker.chunk_document(doc)

        assert len(chunks) >= 2
        assert any(c.section_heading == "Chapter 1" for c in chunks)

@pytest.mark.asyncio
async def test_file_roots_and_scanning_api(client: AsyncClient):
    print("STEP 1: Getting auth token...")
    token = await get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "quarterly_report.txt"
        test_file.write_text("Q3 Financial Overview: Revenue grew by 45% due to SMRITIX AI platform adoption.", encoding="utf-8")

        print("STEP 2: Registering root...")
        reg_res = await client.post(
            "/api/v1/files/roots",
            headers=headers,
            json={
                "root_path": tmpdir,
                "display_name": "Test Reports Vault",
                "is_monitored": True
            }
        )
        print("STEP 2 RES:", reg_res.status_code, reg_res.text)
        assert reg_res.status_code == 201, reg_res.text
        root_data = reg_res.json()["data"] if "data" in reg_res.json() else reg_res.json()
        root_id = root_data["id"]

        print("STEP 3: Listing roots...")
        list_res = await client.get("/api/v1/files/roots", headers=headers)
        assert list_res.status_code == 200
        roots_list = list_res.json()["data"] if "data" in list_res.json() else list_res.json()
        assert any(r["id"] == root_id for r in roots_list)

        print("STEP 4: Listing files...")
        files_res = await client.get(f"/api/v1/files?root_id={root_id}", headers=headers)
        assert files_res.status_code == 200
        file_list = files_res.json()["data"] if "data" in files_res.json() else files_res.json()
        assert file_list["total"] >= 1
        file_rec = file_list["items"][0]
        assert file_rec["file_name"] == "quarterly_report.txt"

        print("STEP 5: Indexing file...")
        file_id = file_rec["id"]
        index_res = await client.post(f"/api/v1/files/{file_id}/reindex", headers=headers)
        assert index_res.status_code == 200

        print("STEP 6: Asking question...")
        ask_res = await client.post(
            "/api/v1/ask/",
            headers=headers,
            json={"query": "What is the revenue growth in the quarterly report?"}
        )
        assert ask_res.status_code == 200
        ask_data = ask_res.json()["data"] if "data" in ask_res.json() else ask_res.json()
        print("STEP 6 SOURCES:", ask_data.get("sources"))
        assert len(ask_data["sources"]) > 0
        file_source = next((s for s in ask_data["sources"] if s.get("source_category") == "file"), None)
        assert file_source is not None
        assert "quarterly_report.txt" in file_source["title"]
