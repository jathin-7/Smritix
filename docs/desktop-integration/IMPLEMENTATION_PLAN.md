# SMRITIX — Windows Desktop & File Intelligence Implementation Plan

## Executive Summary
This document outlines the architectural transformation of **SMRITIX** into a local-first, privacy-respecting Windows desktop application with native filesystem intelligence. SMRITIX will maintain its sovereign personal AI memory foundation while adding approved-folder browsing, background filesystem monitoring, content extraction, vector indexing, hybrid search, and citation-backed cross-document RAG.

---

## 1. Current Architecture Review

### 1.1 Frontend
- **Framework**: Next.js 14 (App Router) + React 18 + TypeScript
- **Styling**: Tailwind CSS 3.4 + Framer Motion 11 + Pearl-White Theme tokens (`#F8F9FC`, embossed honeycomb, glassmorphism)
- **State Management**:
  - `auth-store.ts` (Zustand): User identity, token storage, authentication state
  - `ui-store.ts` (Zustand): Sidebar, theme, and view toggles
  - TanStack React Query v5: Server state caching, optimistic updates, and queries
- **Client API**: `frontend/src/lib/api/client.ts`
  - Fully typed HTTP client with bearer token injection
  - SSE streaming client (`streamAsk`) with event handling (`token`, `sources`, `done`, `error`)

### 1.2 Backend
- **Framework**: FastAPI (Python 3.12+)
- **Database**: SQLite (local development / zero-cloud storage) with PostgreSQL/pgvector support via SQLAlchemy 2.0 Async
- **Embeddings**: `EmbeddingPipeline` with `all-MiniLM-L6-v2` (384-dimensional dense vectors)
  - Ollama Embedding Provider (`nomic-embed-text` / local fallback)
  - Deterministic portable fallback provider for testing and zero-dependency mode
- **Vector Store**: Qdrant integration with SQLite cosine similarity fallback
- **Search & Retrieval**: `SearchService` (BM25 keyword search + Dense Vector search with Reciprocal Rank Fusion)
- **RAG Engine**: `RAGService` with query enhancement, source attribution, streaming responses, and conversation persistence

---

## 2. Proposed Desktop & File Intelligence Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        WINDOWS DESKTOP (TAURI 2)                       │
│                                                                        │
│   ┌───────────────────────────┐      ┌─────────────────────────────┐   │
│   │    Next.js UI (WebView)   │      │   Rust Core (src-tauri)     │   │
│   │                           │      │                             │   │
│   │ • My Digital Space        │◄────►│ • Native Folder Picker      │   │
│   │ • Approved Folder Tree    │ IPC  │ • Secure Path Validator     │   │
│   │ • File Grid / List / View │      │ • Directory Walker & Meta   │   │
│   │ • Indexing Control Bar    │      │ • `notify` File Watcher     │   │
│   │ • Ask SMRITIX with Files  │      │ • Native File Opener (Shell)│   │
│   │ • System Tray Controls    │      │ • System Tray Lifecycle     │   │
│   └─────────────┬─────────────┘      └──────────────┬──────────────┘   │
└─────────────────┼───────────────────────────────────┼──────────────────┘
                  │ HTTP / Bearer Auth                │ Local REST API
                  ▼                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        SMRITIX BACKEND (FASTAPI)                       │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                       Files API Router                         │   │
│   │  /api/v1/files/roots • /api/v1/files/scan • /api/v1/files/jobs │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                   │
│   ┌────────────────────────────────▼───────────────────────────────┐   │
│   │                    File Intelligence Service                   │   │
│   │                                                                │   │
│   │ • FileRegistryService: Manages approved roots, paths & hashes  │   │
│   │ • FileExtractionService: PDF, DOCX, XLSX, PPTX, MD, TXT, Code  │   │
│   │ • FileChunkingService: Structure-aware sliding window chunking │   │
│   │ • FileEmbeddingService: 384-dim dense embeddings (MiniLM)      │   │
│   │ • FileSyncService: Detects modifications, deletes, re-indexes  │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                   │
│   ┌────────────────────────────────▼───────────────────────────────┐   │
│   │                   Unified Knowledge Retrieval                  │   │
│   │                                                                │   │
│   │ • SearchService: Unified Hybrid Ranking (Memories + Files)     │   │
│   │ • RAGService: Context assembly with document citations        │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
└────────────────────────────────────┼───────────────────────────────────┘
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     LOCAL STORAGE & VECTOR PERSISTENCE                 │
│                                                                        │
│ • Database: `file_roots`, `file_records`, `file_versions`,             │
│             `file_chunks`, `file_jobs`, `file_events`                  │
│ • Vectors: Qdrant / Local vector store (same collection or tagged)     │
│ • Filesystem: Original files remain strictly in-place (read-only)      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Responsibilities

| Subsystem | Technology | Responsibility |
|---|---|---|
| **Window & Tray** | Tauri 2 (Rust) | Native window frame, tray menu (pause/resume/status), background persistence when window is closed |
| **Filesystem Access** | Rust (`std::fs`, `windows-sys`) | Native Windows folder selection dialog (`rfd`), directory listing, metadata extraction, launch default viewer |
| **Filesystem Watcher** | Rust (`notify` crate) | Watches approved directories recursively, debounces duplicate events, emits IPC change events |
| **User Interface** | Next.js 14, React 18, Tailwind | "My Digital Space" route, directory explorer, file previews, sync monitoring, citation viewer |
| **File Intelligence** | FastAPI (Python) | Text extraction (PDF, Office, Markdown, code), SHA-256 deduplication, chunking, embedding generation |
| **Unified RAG** | Python (`RAGService`) | Cross-document retrieval, citing both memories and indexed file chunks with clickable file launchers |

---

## 4. Database Schema Changes

The following new entities will be added to the database via SQLAlchemy models:

### 4.1 `file_roots`
Tracks user-approved directory roots.
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id)
- `root_path` (String, unique per user)
- `display_name` (String)
- `is_monitored` (Boolean, default True)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### 4.2 `file_records`
Tracks individual files discovered within approved roots.
- `id` (UUID, PK)
- `root_id` (UUID, FK -> file_roots.id)
- `relative_path` (String)
- `file_name` (String)
- `extension` (String)
- `file_size` (Integer)
- `content_hash` (String, SHA-256)
- `modified_at` (DateTime)
- `indexed_at` (DateTime, nullable)
- `indexing_status` (String: `pending`, `indexing`, `indexed`, `failed`, `skipped`)
- `error_message` (Text, nullable)

### 4.3 `file_chunks`
Vector-indexed text chunks derived from approved documents.
- `id` (UUID, PK)
- `file_id` (UUID, FK -> file_records.id)
- `chunk_index` (Integer)
- `page_number` (Integer, nullable)
- `section_heading` (String, nullable)
- `content` (Text)
- `token_count` (Integer)
- `embedding_id` (String, nullable)
- `metadata_json` (JSON, nullable)

### 4.4 `file_jobs`
Asynchronous background tracking for indexing tasks.
- `id` (UUID, PK)
- `file_id` (UUID, FK -> file_records.id)
- `job_type` (String: `index`, `reindex`, `delete`)
- `status` (String: `queued`, `processing`, `completed`, `failed`)
- `retry_count` (Integer)
- `error` (Text, nullable)
- `created_at` (DateTime)
- `completed_at` (DateTime, nullable)

---

## 5. Security & Privacy Architecture

1. **Explicit Root Whitelist**: Rust IPC strictly enforces that only canonicalized subpaths of user-approved roots can be browsed, read, or watched. Path traversal (`..`), junctions to unapproved volumes, and symlink escapes are immediately rejected.
2. **Read-Only Operation**: SMRITIX operates as a read-only reader of local files. It never modifies, moves, or writes back to user document folders.
3. **Localhost Network Binding**: FastAPI and Next.js bind strictly to `127.0.0.1` / loopback with JWT authentication.
4. **Zero Cloud Egress**: Document extraction and embedding run 100% locally on-device. No document text or file paths are ever transmitted externally.
5. **Private Folder Exclusions**: Automatically excludes system folders (`AppData`, `Windows`, `Program Files`, `.git`, `.venv`, `node_modules`, temporary files, credentials).

---

## 6. Implementation Sequence

1. **Phase 0: Repository Audit & Planning** (Completed in this document)
2. **Phase 1: Tauri 2 Desktop Foundation**
   - Initialize `src-tauri` with Tauri 2 configuration.
   - Configure window lifecycle, native permissions, and capabilities.
3. **Phase 2: Native Windows Filesystem Bridge in Rust**
   - Implement Tauri commands: `select_folder`, `list_directory`, `get_file_metadata`, `open_file_native`, `validate_path`.
4. **Phase 3: My Digital Space Frontend UI**
   - Create `/space` primary navigation and dashboard in Next.js.
   - Implement `FileBrowser`, `FileGrid`, `FileList`, `FilePreview`, `FolderConnectionDialog`, and `IndexingStatus`.
5. **Phase 4: Automatic Rust File Watcher**
   - Implement background watcher with `notify` crate, event debouncer, and reconciliation worker.
6. **Phase 5: Backend File Intelligence Pipeline**
   - Implement `FileExtractionService` supporting PDF, DOCX, XLSX, PPTX, TXT, MD, and source code.
   - Implement `FileChunkingService` with heading & page preservation.
   - Implement `FileRegistryService` with SHA-256 deduplication and change reconciliation.
7. **Phase 6: Database Models & Migrations**
   - Add SQLAlchemy models and register them with metadata.
8. **Phase 7: FastAPI Files Router**
   - Endpoints: `/api/v1/files/roots`, `/api/v1/files`, `/api/v1/files/scan`, `/api/v1/files/{id}/reindex`.
9. **Phase 8: Connect Files to Memory & RAG Retrieval**
   - Update `SearchService` to return file chunks alongside memories.
   - Update `RAGService` to generate citations with clickable file launchers.
10. **Phase 9: Windows System Tray & Lifecycle**
    - Implement background tray menu with pause, resume, status, and exit.
11. **Phase 10: Verification & Testing**
    - End-to-end integration test: folder approval -> file addition -> auto extraction -> Ask SMRITIX retrieval with citation.

---

## 7. Verification Strategy
- **Backend Pytest**: Unit and integration tests for extraction, chunking, file registry, and search retrieval.
- **Frontend Type Check & Lint**: Strict TypeScript validation (`tsc --noEmit`) and Next.js production build (`next build`).
- **End-to-End Workflow**: Connect folder -> Drop PDF -> Verify indexing -> Ask query -> Receive cited answer.
