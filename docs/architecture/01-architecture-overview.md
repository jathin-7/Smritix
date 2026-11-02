# SMRITIX — Architecture Overview

> **"Remember. Connect. Rediscover."**
>
> Personal AI Memory System — Technical Blueprint v1.0

---

## 1. What Is SMRITIX?

SMRITIX is a **local-first, privacy-first, AI-powered Personal Memory System**. It ingests a user's digital knowledge — notes, documents, code, conversations, voice — organises it into structured memories with semantic search and a knowledge graph, and lets the user query, explore, and rediscover their own knowledge through natural language.

---

## 2. Design Principles

| # | Principle | Implication |
|---|-----------|-------------|
| 1 | **Local-first** | All core features work without internet. Data lives on the user's machine by default. |
| 2 | **Privacy-first** | No data leaves the device unless the user explicitly opts in to a cloud AI provider. |
| 3 | **AI-agnostic** | Abstract provider layer — swap between Ollama, OpenAI, Anthropic, Google, etc. |
| 4 | **Zero-cost dev** | V1 runs entirely on free, local tools (Ollama, Qdrant, PostgreSQL, Whisper). |
| 5 | **Modular** | Every subsystem (ingestion, search, RAG, graph, voice) is a replaceable module. |
| 6 | **User-controlled** | The user decides what SMRITIX can access, index, and remember. |
| 7 | **Progressive complexity** | V1 is simple. Each version adds capability without rewriting foundations. |

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SMRITIX FRONTEND                            │
│              Next.js 14+ · React · TypeScript · Tailwind            │
│     ┌──────────┬──────────┬──────────┬────────────┬──────────┐      │
│     │Dashboard │ Memories │  Ask AI  │ Knowledge  │  Voice   │      │
│     │          │ & Search │  (Chat)  │   Graph    │          │      │
│     └────┬─────┴────┬─────┴────┬─────┴─────┬──────┴────┬─────┘      │
│          │          │          │           │          │              │
│          └──────────┴──────────┴───────────┴──────────┘              │
│                              │  REST / SSE / WebSocket              │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         SMRITIX BACKEND                              │
│                    Python · FastAPI · Async                           │
│                                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────────┐  │
│  │   Router    │  │  Service   │  │ Repository │  │ Infrastructure│  │
│  │   Layer     │──│  Layer     │──│  Layer     │──│    Layer      │  │
│  │ (Pydantic)  │  │ (Business) │  │ (DB/ORM)   │  │ (AI/Vector)  │  │
│  └────────────┘  └────────────┘  └────────────┘  └───────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    AI ABSTRACTION LAYER                          │ │
│  │  ┌─────────┐ ┌───────────┐ ┌─────────┐ ┌─────────┐            │ │
│  │  │   LLM   │ │ Embedding │ │   STT   │ │   TTS   │            │ │
│  │  │Provider │ │ Provider  │ │Provider │ │Provider │            │ │
│  │  └────┬────┘ └─────┬─────┘ └────┬────┘ └────┬────┘            │ │
│  │       │            │            │            │                  │ │
│  │  ┌────▼────┐ ┌─────▼─────┐ ┌────▼────┐ ┌────▼────┐            │ │
│  │  │ Ollama  │ │MiniLM/Ada │ │ Whisper │ │  Piper  │            │ │
│  │  │ OpenAI  │ │ Cohere    │ │Deepgram │ │Eleven   │            │ │
│  │  │Anthropic│ │           │ │         │ │Labs     │            │ │
│  │  └─────────┘ └───────────┘ └─────────┘ └─────────┘            │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌──────────────────────────────────┐  ┌──────────────────────────┐ │
│  │        PIPELINES                 │  │     BACKGROUND JOBS      │ │
│  │  • Document Ingestion            │  │  • Celery / BackgroundTasks│
│  │  • Memory Creation               │  │  • Connection Discovery   │ │
│  │  • RAG (Retrieval + Generation)  │  │  • Auto-tagging           │ │
│  │  • Code Ingestion                │  │  • Re-embedding           │ │
│  │  • Voice Transcription           │  │  • Knowledge gap scan     │ │
│  └──────────────────────────────────┘  └──────────────────────────┘ │
└────────────────┬──────────────┬──────────────┬───────────────────────┘
                 │              │              │
        ┌────────▼──────┐ ┌────▼─────┐ ┌──────▼───────┐
        │  PostgreSQL   │ │  Qdrant  │ │ File Storage │
        │  (Data + FTS  │ │ (Vectors)│ │  (Local FS)  │
        │  + KG edges)  │ │          │ │              │
        └───────────────┘ └──────────┘ └──────────────┘
```

---

## 4. Technology Choices & Reasoning

### Frontend

| Technology | Purpose | Why |
|-----------|---------|-----|
| **Next.js 14+ (App Router)** | Framework | SSR/SSG, file-based routing, API routes, excellent DX |
| **React 18+** | UI | Component model, ecosystem, hooks |
| **TypeScript** | Type safety | Catches bugs at compile time, self-documenting |
| **Tailwind CSS** | Styling | Utility-first, fast iteration, small bundle |
| **TanStack Query** | Server state | Caching, deduplication, background refetch |
| **Zustand** | Client state | Tiny, no boilerplate, performant |
| **React Hook Form + Zod** | Forms | Uncontrolled for performance, schema validation |
| **TipTap** | Rich text editor | Extensible, ProseMirror-based, markdown support |
| **Framer Motion** | Animations | Declarative, layout animations, spring physics |
| **GSAP** | Complex animations | Timeline control, scroll triggers, landing page |
| **Lenis** | Smooth scrolling | Lightweight, performant |
| **Three.js / R3F / Drei** | 3D visualization | Knowledge graph 3D view, landing page |

### Backend

| Technology | Purpose | Why |
|-----------|---------|-----|
| **Python 3.12+** | Language | AI/ML ecosystem, FastAPI, async support |
| **FastAPI** | Framework | Async, auto OpenAPI docs, Pydantic, dependency injection |
| **SQLAlchemy 2.0 (async)** | ORM | Mature, async support, type hints |
| **Alembic** | Migrations | Standard for SQLAlchemy, version-controlled schema |
| **Pydantic v2** | Validation | Request/response models, settings, fast |
| **Celery + Redis** | Task queue | Heavy background jobs (ingestion, batch embedding) |
| **Python-Jose / PyJWT** | Auth | JWT token handling |
| **Passlib + Bcrypt** | Password hashing | Industry standard |

### Data Layer

| Technology | Purpose | Why |
|-----------|---------|-----|
| **PostgreSQL 16** | Primary database | JSONB, full-text search (tsvector), recursive CTEs for graph traversal, RLS, mature |
| **Qdrant** | Vector database | Production-ready, filtering, payload support, hybrid search, Docker-native, better than Chroma for production |
| **Redis** | Cache + task broker | Session cache, rate limiting, Celery broker |
| **Local filesystem** | File storage | Uploaded documents, audio files. V2: S3-compatible (MinIO) |

### AI Layer

| Technology | Purpose | Why |
|-----------|---------|-----|
| **Ollama** | Local LLM runtime | Simple API, model management, runs llama3/mistral locally |
| **sentence-transformers** | Local embeddings | all-MiniLM-L6-v2 — fast, 384-dim, good quality |
| **faster-whisper** | Local STT | CTranslate2-optimized Whisper, fast on CPU |
| **Piper TTS** | Local TTS | Lightweight, runs on CPU, good quality |

---

## 5. Version Roadmap

### V1 — MVP: "The Memory That Works"

**Goal:** Users can create, store, search, and ask questions about their memories.

| Feature | Scope |
|---------|-------|
| User auth | JWT, single-user mode |
| Manual memory creation | Text-based, with tags |
| Document ingestion | PDF, Markdown, TXT |
| Chunking + embedding | Local sentence-transformers |
| Semantic search | Qdrant vector search |
| Full-text search | PostgreSQL tsvector |
| Ask SMRITIX (RAG) | Basic RAG with source attribution |
| Knowledge graph | PostgreSQL edges, basic connections |
| Dashboard | Memory counts, recent memories |
| Memory detail view | View, edit, delete, see connections |
| Local AI only | Ollama + local embeddings |

**Not in V1:** Voice, 3D graph, auto-tagging, code ingestion, timeline, learning map, knowledge gaps.

### V1.5 — "Connected Intelligence"

| Feature | Scope |
|---------|-------|
| Auto-connection discovery | AI-powered similarity edges |
| Auto-tagging | LLM-generated tag suggestions |
| Auto-summarization | LLM-generated summaries |
| Projects | Group memories into projects |
| Cloud AI providers | OpenAI, Anthropic, Google options |
| Voice transcription | Upload audio → memory |
| URL ingestion | Web page → memory |
| Knowledge graph visualization | 2D force-directed graph |
| Memory timeline | Chronological view |
| Hybrid search | Combined semantic + full-text with RRF |

### V2 — "Your Second Brain"

| Feature | Scope |
|---------|-------|
| Code/repository ingestion | tree-sitter, AST-aware |
| 3D knowledge graph | Three.js visualization |
| Real-time voice conversation | WebSocket STT → RAG → TTS |
| Learning map | Skill/topic progression tracking |
| Knowledge gap detection | Graph analysis for missing areas |
| Browser extension | Auto-capture web content |
| API keys for integrations | Programmatic access |
| Neo4j option | Optional graph database upgrade |
| Multi-user | Multiple accounts, sharing |

### Future

| Feature | Scope |
|---------|-------|
| Mobile app | React Native or PWA |
| Team memory | Shared organizational knowledge |
| Plugin system | Third-party integrations |
| Cloud deployment | Managed SaaS option |
| Custom fine-tuned models | Domain-specific AI |
| Multi-language support | i18n |
| Export/import | Full data portability |
| End-to-end encryption | At-rest encryption |

---

## 6. Core Data Flow Diagrams

### 6.1 Memory Creation Flow

```
User creates memory (via UI or API)
        │
        ▼
┌─────────────────┐
│  Validate Input  │
│  (Pydantic)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Store Memory     │────▶│  PostgreSQL      │
│ (title, content, │     │  memories table  │
│  tags, source)   │     └─────────────────┘
└────────┬────────┘
         │
         ▼  (Background Task)
┌─────────────────┐
│  Chunk Content   │
│  (512 tokens,    │
│   50 overlap)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Generate         │────▶│  Qdrant          │
│ Embeddings       │     │  (vector store)  │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Discover         │────▶│  knowledge_edges │
│ Connections      │     │  table           │
│ (vector search   │     └─────────────────┘
│  for similar)    │
└─────────────────┘
```

### 6.2 Document Ingestion Flow

```
User uploads document (PDF/MD/TXT/DOCX)
        │
        ▼
┌─────────────────┐     ┌─────────────────┐
│ Create Ingestion │────▶│ ingestion_jobs   │
│ Job (pending)    │     │ status: pending  │
└────────┬────────┘     └─────────────────┘
         │
         ▼  (Celery Worker / Background Task)
┌─────────────────┐
│ Extract Content  │  ← PyMuPDF / python-docx / BeautifulSoup
│ + Metadata       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Clean &          │
│ Normalize        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Create Memory    │  → enters Memory Creation Flow above
│ Record           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AI Summarize     │  ← LLMProvider.complete()
│ + Auto-tag       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update Job       │  → status: completed
│ Status           │
└─────────────────┘
```

### 6.3 Ask SMRITIX (RAG) Flow

```
User asks: "What did I learn about distributed systems?"
        │
        ▼
┌─────────────────┐
│ Query Enhancement│  ← LLM expands query into search variants
│ + Intent Detection│
└────────┬────────┘
         │
         ├──────────────┐
         ▼              ▼
┌──────────────┐ ┌──────────────┐
│ Semantic      │ │ Full-text    │
│ Search        │ │ Search       │
│ (Qdrant)      │ │ (PostgreSQL) │
└──────┬───────┘ └──────┬───────┘
       │                │
       └────────┬───────┘
                ▼
┌─────────────────┐
│ Merge + Dedup   │
│ Reciprocal Rank │
│ Fusion (RRF)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Knowledge Graph  │  ← traverse edges from top results
│ Expansion        │     to find related memories
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Context Assembly │  ← select top-N chunks, respect token limit
│ + Source Metadata│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM Generation  │  ← system prompt: "cite sources as [1], [2]..."
│ (streaming SSE) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Source           │  ← map [1] → memory_id, return structured response
│ Attribution      │
└─────────────────┘

Response: {
  answer: "Based on your notes from March, you studied...",
  sources: [
    { memory_id: "...", title: "Distributed Systems Notes", relevance: 0.92 },
    { memory_id: "...", title: "CAP Theorem Summary", relevance: 0.87 }
  ]
}
```

### 6.4 Semantic Search Flow

```
User query: "machine learning optimization"
        │
        ▼
┌─────────────────┐
│ Embed Query      │  ← EmbeddingProvider.embed([query])
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Qdrant Search    │  ← search(vector, filter={user_id}, top_k=20)
│ (with filters)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Hydrate Results  │  ← join with PostgreSQL for full memory data
│ (memory details) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return ranked    │
│ results with     │
│ similarity scores│
└─────────────────┘
```

---

## 7. V1 Implementation Order

Execute in this sequence. Each phase builds on the previous.

```
Phase 0: Foundation          (Week 1)
├── Project scaffolding (monorepo structure)
├── Docker Compose (PostgreSQL + Qdrant + Redis)
├── FastAPI app skeleton with health check
├── Next.js app skeleton with Tailwind
├── Database schema + Alembic migrations
└── CI: linting, type checking

Phase 1: Auth + Core CRUD    (Week 2)
├── User registration + login (JWT)
├── Memory CRUD API
├── Memory list page (frontend)
├── Memory create/edit page
├── Memory detail page
└── Tag CRUD

Phase 2: Ingestion           (Week 3)
├── AI abstraction layer (interfaces + Ollama provider)
├── Local embedding provider (sentence-transformers)
├── Chunking pipeline
├── Embedding pipeline
├── Document ingestion (PDF, Markdown, TXT)
├── Ingestion job tracking
└── Background task execution

Phase 3: Search              (Week 4)
├── Qdrant integration
├── Semantic search endpoint
├── Full-text search (PostgreSQL tsvector)
├── Search UI with filters
└── Search history

Phase 4: Ask SMRITIX (RAG)   (Week 5)
├── RAG pipeline (retrieval → context → generation)
├── Source attribution
├── Chat conversation UI
├── Streaming responses (SSE)
├── Conversation history
└── Query enhancement

Phase 5: Knowledge Graph     (Week 6)
├── knowledge_edges table + API
├── Auto-connection discovery on memory creation
├── Memory connections view
├── Basic graph visualization (2D, using react-force-graph)
└── Manual edge creation

Phase 6: Dashboard + Polish  (Week 7)
├── Dashboard stats
├── Recent memories feed
├── Memory type breakdown
├── Settings page (AI provider config)
├── Error handling polish
├── Loading states + empty states
└── Documentation

Phase 7: Testing + Hardening (Week 8)
├── Backend unit tests (pytest)
├── Backend integration tests
├── Frontend component tests (Vitest)
├── E2E tests (Playwright)
├── Security audit
├── Performance profiling
└── README + setup guide
```

---

## 8. Subsystem Document Index

| # | Document | Covers |
|---|----------|--------|
| 01 | This document | Architecture overview, tech choices, data flows, roadmap |
| 02 | [Security & Privacy](./02-security-privacy.md) | Auth, encryption, RLS, privacy controls, threat model |
| 03 | [Database Schema](./03-database-schema.md) | PostgreSQL schema, vector DB design, knowledge graph |
| 04 | [API Design](./04-api-design.md) | REST API, request/response formats, backend architecture |
| 05 | [AI & Pipelines](./05-ai-and-pipelines.md) | AI abstraction, ingestion, RAG, auto-memory, voice |
| 06 | [Frontend Architecture](./06-frontend-architecture.md) | Next.js structure, components, state, animations |
| 07 | [Folder Structure](./07-folder-structure.md) | Complete project directory layout |
| 08 | [Risks & Performance](./08-risks-performance.md) | Technical risks, performance strategy, scalability |

---

## 9. Local Development Stack (Zero Cost)

All V1 services run locally with zero cloud dependencies:

```
┌─────────────────────────────────────────┐
│           docker-compose.yml            │
├─────────────────────────────────────────┤
│  ┌───────────┐  ┌───────────┐          │
│  │ PostgreSQL │  │  Qdrant   │          │
│  │  :5432     │  │  :6333    │          │
│  └───────────┘  └───────────┘          │
│  ┌───────────┐  ┌───────────┐          │
│  │   Redis   │  │  Ollama   │          │
│  │  :6379    │  │  :11434   │          │
│  └───────────┘  └───────────┘          │
├─────────────────────────────────────────┤
│  Running natively:                      │
│  ┌─────────────┐  ┌──────────────┐     │
│  │ FastAPI      │  │ Next.js dev  │     │
│  │ (uvicorn)    │  │ server       │     │
│  │ :8000        │  │ :3000        │     │
│  └─────────────┘  └──────────────┘     │
└─────────────────────────────────────────┘
```

**System requirements for V1 development:**
- 8 GB RAM minimum (16 GB recommended for Ollama)
- Docker Desktop
- Node.js 20+
- Python 3.12+
- ~10 GB disk (Ollama models + PostgreSQL + Qdrant)

---

## 10. Future Cloud Deployment Architecture

When ready for cloud deployment:

```
                    ┌──────────────┐
                    │  Cloudflare   │
                    │  (CDN + WAF) │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼                         ▼
     ┌────────────────┐      ┌────────────────┐
     │  Next.js        │      │  FastAPI        │
     │  (Vercel or     │      │  (Cloud Run or  │
     │   container)    │      │   ECS/Fly.io)   │
     └────────────────┘      └────────┬────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                  ▼
           ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
           │  Cloud SQL   │  │ Qdrant Cloud │  │  Cloud       │
           │ (PostgreSQL) │  │  or Pinecone │  │  Storage     │
           └──────────────┘  └──────────────┘  │  (S3/GCS)   │
                                                └──────────────┘
```

---

*This is a living document. Update as architecture decisions are refined during implementation.*
