# SMRITIX — Risks, Performance & Scalability

> Document 08 of the SMRITIX Technical Blueprint

---

## 1. Technical Risks

### 1.1 Critical Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| R1 | **Local LLM quality insufficient** | RAG answers are poor, users lose trust | High | Design AI layer so cloud models are one config change away. Benchmark Ollama models against cloud. Set quality floor — if local model can't meet it, recommend cloud. |
| R2 | **Embedding model mismatch** | Changing embedding model requires re-embedding ALL memories | High | Lock embedding model per collection. Track model version in metadata. Build re-embedding migration tool from Day 1. |
| R3 | **Chunking strategy loses context** | Retrieved chunks miss important context, RAG answers are incomplete | Medium | Use overlap (50 tokens). Include parent document metadata. Test with real documents during development. Consider parent-child retrieval (return surrounding chunks). |
| R4 | **PostgreSQL knowledge graph doesn't scale** | Graph queries become slow with 100K+ edges | Medium | Recursive CTEs with depth limits. Materialized views for common queries. Monitor query times. Neo4j adapter ready for V2. |
| R5 | **Voice transcription accuracy** | Local Whisper produces bad transcripts on CPU | Medium | Use `faster-whisper` with CTranslate2. Default to `base` or `small` model. Allow user to select model size. Cloud fallback (Deepgram). |

### 1.2 Architecture Risks

| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| R6 | **Over-abstraction in AI layer** | Complexity slows development | Keep V1 interfaces minimal (4 methods). Only abstract what's needed now. Refactor when adding second provider. |
| R7 | **Monorepo complexity** | Frontend/backend coupling, slow CI | Clear separation via `frontend/` and `backend/` dirs. Independent build pipelines. Shared types via OpenAPI spec generation, not code sharing. |
| R8 | **Background job reliability** | Ingestion jobs fail silently | Job status tracking in DB. Retry logic with exponential backoff. Dead letter queue for permanent failures. UI shows job status. |
| R9 | **Data migration during schema evolution** | Breaking changes lose data | Alembic migrations from Day 1. Never delete columns — deprecate first. Test migrations against production-sized data. |
| R10 | **Scope creep in V1** | Never ships | Strictly enforce V1 feature boundary. Every feature proposal must answer: "Does this make the core memory→search→ask loop work better?" |

### 1.3 Operational Risks

| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| R11 | **Docker resource consumption** | PostgreSQL + Qdrant + Ollama + Redis uses too much RAM | Profile resource usage. Provide `docker-compose.light.yml` without Ollama (use external instance). Document minimum specs. |
| R12 | **Qdrant data loss** | Vector store corruption loses all embeddings | Docker volume persistence. Backup strategy. Re-embedding from PostgreSQL chunks as disaster recovery. |
| R13 | **Slow first-time setup** | Users abandon before trying | One-command setup (`make setup`). Pre-configured `.env.example`. Health check endpoint that verifies all services. |

---

## 2. Performance Architecture

### 2.1 Performance Targets (V1)

| Operation | Target Latency | Notes |
|-----------|---------------|-------|
| Memory CRUD | < 100ms | Standard DB operations |
| Semantic search (vector) | < 200ms | Qdrant search with 100K vectors |
| Full-text search | < 150ms | PostgreSQL tsvector with GIN index |
| Hybrid search | < 400ms | Combined semantic + full-text + RRF |
| RAG (Ask SMRITIX) | < 3s to first token | Retrieval + context assembly + LLM streaming |
| Document ingestion | < 30s for 10-page PDF | Extract + chunk + embed |
| Embedding generation | < 500ms per chunk | Local sentence-transformers (batch) |
| Page load (frontend) | < 1s (LCP) | Next.js SSR + code splitting |
| Voice transcription | < 2x real-time | 30s audio → < 60s processing |

### 2.2 Database Performance

#### Indexes

```sql
-- Critical indexes (already in schema doc, summarized here)
-- Foreign keys (all FKs indexed)
-- Composite indexes for common queries
CREATE INDEX idx_memories_user_type     ON memories(user_id, memory_type);
CREATE INDEX idx_memories_user_created  ON memories(user_id, created_at DESC);
CREATE INDEX idx_memories_content_hash  ON memories(content_hash);

-- Full-text search
CREATE INDEX idx_memories_fts ON memories USING GIN(
  to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, ''))
);

-- Knowledge graph traversal
CREATE INDEX idx_edges_source ON knowledge_edges(source_memory_id);
CREATE INDEX idx_edges_target ON knowledge_edges(target_memory_id);
CREATE INDEX idx_edges_user   ON knowledge_edges(user_id);
```

#### Connection Pooling

```python
# SQLAlchemy async connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Concurrent connections
    max_overflow=10,       # Extra connections under load
    pool_timeout=30,       # Wait for connection
    pool_recycle=1800,     # Recycle connections every 30 min
    echo=False,            # No SQL logging in production
)
```

#### Query Optimization

- **Pagination:** Cursor-based (keyset), not OFFSET — O(1) vs O(n)
- **Eager loading:** Use `selectinload` for related objects (avoid N+1)
- **Projections:** Select only needed columns for list views
- **Materialized views:** For dashboard statistics (refresh periodically)

### 2.3 Vector Search Performance

#### Qdrant Configuration

```yaml
# Collection configuration for V1
collection:
  vectors:
    size: 384                    # all-MiniLM-L6-v2 dimensions
    distance: Cosine
  optimizers:
    default_segment_number: 2    # Good for < 1M vectors
    indexing_threshold: 20000    # Build HNSW index after 20K vectors
  hnsw_config:
    m: 16                        # Connections per node (default)
    ef_construct: 100            # Build-time accuracy
    ef: 128                      # Search-time accuracy (higher = more accurate, slower)
```

#### Search Optimization

- **Filtering before search:** Use Qdrant payload filters (user_id) to narrow search space
- **Batch queries:** Embed query once, search in single request
- **Limit top_k:** Default 20, max 100
- **Caching:** Cache frequent query embeddings in Redis (TTL: 5 min)

### 2.4 Embedding Performance

```python
# Batch embedding for ingestion (not one-at-a-time)
class LocalEmbeddingProvider:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        # Pre-load to GPU if available
        self.model.to('cuda' if torch.cuda.is_available() else 'cpu')

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Batch encode — much faster than individual calls
        embeddings = self.model.encode(
            texts,
            batch_size=64,
            show_progress_bar=False,
            normalize_embeddings=True,  # For cosine similarity
        )
        return embeddings.tolist()
```

**Key decisions:**
- Batch size: 64 (balance between throughput and memory)
- Normalize embeddings at encode time (faster cosine similarity)
- GPU acceleration when available
- Model loaded once at startup (not per-request)

### 2.5 Frontend Performance

| Strategy | Implementation |
|----------|---------------|
| **Code splitting** | Next.js App Router automatic route-based splitting |
| **Lazy loading** | Dynamic imports for heavy components (Three.js, TipTap) |
| **Image optimization** | Next.js `<Image>` component |
| **Bundle analysis** | `@next/bundle-analyzer` in CI |
| **Caching** | TanStack Query with stale-while-revalidate |
| **Virtualization** | `react-window` for long memory lists |
| **Debouncing** | Search input debounced (300ms) |
| **Prefetching** | Prefetch likely next pages on hover |

### 2.6 Caching Strategy

```
┌─────────────────────────────────────────────┐
│              Caching Layers                 │
├─────────────────────────────────────────────┤
│                                             │
│  L1: React Query Cache (Frontend)           │
│      • Stale time: 30s (memories list)      │
│      • Stale time: 5min (dashboard stats)   │
│      • Infinite stale (memory detail)       │
│      • Invalidate on mutation               │
│                                             │
│  L2: Redis Cache (Backend)                  │
│      • Dashboard stats: 5 min TTL           │
│      • User settings: 10 min TTL            │
│      • Query embeddings: 5 min TTL          │
│      • Rate limit counters: sliding window  │
│                                             │
│  L3: Database (PostgreSQL)                  │
│      • Materialized views for aggregations  │
│      • Refreshed every 15 minutes           │
│                                             │
│  L4: Qdrant (Vector Cache)                  │
│      • In-memory HNSW index                 │
│      • Persisted to disk on snapshot        │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 3. Scalability Strategy

### 3.1 Scalability Tiers

| Tier | Users | Memories | Vectors | Infrastructure |
|------|-------|----------|---------|---------------|
| **Tier 1: Personal** | 1 | < 10K | < 100K | Single Docker Compose on laptop |
| **Tier 2: Power User** | 1 | < 100K | < 1M | Single server, 16GB RAM |
| **Tier 3: Small Team** | < 10 | < 500K | < 5M | Single server, 32GB RAM, separate DB |
| **Tier 4: Organization** | < 100 | < 5M | < 50M | Kubernetes, managed databases |
| **Tier 5: SaaS** | 1000+ | Unlimited | Unlimited | Fully managed cloud infrastructure |

### 3.2 Scaling Path

```
Tier 1 (V1)                    Tier 2-3 (V1.5-V2)              Tier 4-5 (Future)
─────────────                  ──────────────────               ─────────────────

All-in-one Docker Compose  →   Separate DB instances       →   Kubernetes / Cloud
                                                                
├─ PostgreSQL (embedded)       ├─ PostgreSQL (dedicated)       ├─ Cloud SQL / RDS
├─ Qdrant (embedded)           ├─ Qdrant (dedicated, replicas) ├─ Qdrant Cloud / Pinecone
├─ Redis (embedded)            ├─ Redis (dedicated)            ├─ Redis Cloud / Memorystore
├─ Ollama (local)              ├─ Ollama (GPU server)          ├─ vLLM / Cloud AI APIs
└─ FastAPI (single process)    └─ FastAPI (multiple workers)   └─ FastAPI (auto-scaled pods)
```

### 3.3 What Scales First (Bottleneck Analysis)

```
Expected bottleneck order:

1. Embedding generation (CPU-bound)
   → Mitigation: Batch processing, GPU, cloud embedding API

2. LLM inference (CPU/GPU-bound)
   → Mitigation: Ollama with GPU, cloud LLM fallback

3. Vector search (memory-bound at scale)
   → Mitigation: Qdrant sharding, increased RAM

4. PostgreSQL (I/O-bound at very high scale)
   → Mitigation: Connection pooling, read replicas, partitioning

5. File storage (disk I/O)
   → Mitigation: S3-compatible storage (MinIO → S3/GCS)
```

### 3.4 Database Scaling Strategy

| Scale Point | Action |
|------------|--------|
| < 100K rows | Default PostgreSQL, no special tuning |
| 100K–1M rows | Add indexes, tune `shared_buffers`, `work_mem` |
| 1M–10M rows | Table partitioning (by user_id or date), connection pooling (PgBouncer) |
| 10M+ rows | Read replicas, or migrate to managed cloud DB |

### 3.5 Vector Database Scaling

| Scale Point | Action |
|------------|--------|
| < 100K vectors | Single Qdrant instance, default config |
| 100K–1M vectors | Tune HNSW params, increase RAM allocation |
| 1M–10M vectors | Qdrant cluster mode (multiple shards) |
| 10M+ vectors | Qdrant Cloud or Pinecone |

---

## 4. Monitoring & Observability (V1.5+)

### 4.1 Health Checks

```python
# GET /api/v1/health
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": { "status": "up", "latency_ms": 2 },
    "qdrant":   { "status": "up", "latency_ms": 5 },
    "redis":    { "status": "up", "latency_ms": 1 },
    "ollama":   { "status": "up", "models": ["llama3"] }
  }
}
```

### 4.2 Metrics to Track

| Category | Metrics |
|----------|---------|
| **API** | Request count, latency (p50/p95/p99), error rate per endpoint |
| **Database** | Query latency, connection pool utilization, slow queries |
| **Vector Search** | Search latency, result count, cache hit rate |
| **AI** | Inference latency, tokens used, provider errors |
| **Ingestion** | Jobs queued, processing time, failure rate |
| **Business** | Memories created/day, searches/day, questions asked/day |

### 4.3 Logging

```python
# Structured JSON logging
import structlog

logger = structlog.get_logger()

logger.info(
    "memory.created",
    user_id=str(user_id),
    memory_id=str(memory_id),
    memory_type=memory_type,
    chunk_count=chunk_count,
    duration_ms=duration_ms,
)
```

V1: stdout (structured JSON) → `docker logs`  
V2: ELK stack or Grafana Loki  

---

## 5. Testing Strategy

### 5.1 Test Pyramid

```
          ┌──────────┐
          │   E2E    │  ← Playwright: critical user flows
          │  (few)   │     Memory creation → search → ask
          ├──────────┤
          │Integration│  ← pytest: API endpoints with real DB
          │ (medium)  │     Ingestion pipeline end-to-end
          ├──────────┤
          │   Unit    │  ← pytest: services, pipelines, utils
          │  (many)   │     Vitest: React components, hooks
          └──────────┘
```

### 5.2 Test Infrastructure

| Tool | Purpose |
|------|---------|
| **pytest** | Backend unit + integration tests |
| **pytest-asyncio** | Async test support |
| **Testcontainers** | Spin up PostgreSQL + Qdrant in Docker for integration tests |
| **Factory Boy** | Test data factories |
| **Vitest** | Frontend unit tests |
| **React Testing Library** | Component tests |
| **Playwright** | E2E browser tests |
| **MSW (Mock Service Worker)** | Frontend API mocking |

### 5.3 CI Pipeline

```
Push to main →
  ├── Lint (ruff + eslint)
  ├── Type check (mypy + tsc)
  ├── Backend unit tests (pytest)
  ├── Backend integration tests (pytest + testcontainers)
  ├── Frontend unit tests (vitest)
  ├── Build check (next build)
  └── E2E tests (playwright, on merge to main only)
```

---

## 6. Disaster Recovery

### 6.1 Backup Strategy (V1 — Local)

```bash
# Automated daily backup script
#!/bin/bash
BACKUP_DIR="$HOME/.smritix/backups/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

# PostgreSQL dump
docker exec smritix-postgres pg_dump -U smritix smritix > "$BACKUP_DIR/db.sql"

# Qdrant snapshot
curl -X POST "http://localhost:6333/collections/memories/snapshots"

# Copy uploaded files
cp -r ./data/uploads "$BACKUP_DIR/uploads"

# Retain last 30 days
find "$HOME/.smritix/backups" -maxdepth 1 -mtime +30 -exec rm -rf {} \;
```

### 6.2 Recovery Scenarios

| Scenario | Recovery |
|----------|----------|
| Qdrant data loss | Re-embed all chunks from PostgreSQL `memory_chunks` table |
| PostgreSQL corruption | Restore from pg_dump backup |
| File storage loss | Source files lost; metadata and chunks remain in DB |
| Complete data loss | Restore from full backup or re-ingest from source documents |

**Critical insight:** PostgreSQL is the source of truth. Qdrant can always be rebuilt from it. This makes the system resilient.

---

## 7. Development Workflow

### 7.1 Branch Strategy

```
main ← production-ready
  └── develop ← integration branch
        ├── feature/memory-crud
        ├── feature/semantic-search
        ├── feature/rag-pipeline
        └── fix/chunking-boundary
```

### 7.2 Code Quality

| Tool | Purpose |
|------|---------|
| **ruff** | Python linting + formatting (replaces flake8 + black + isort) |
| **mypy** | Python type checking |
| **eslint** | TypeScript/React linting |
| **prettier** | Frontend formatting |
| **pre-commit** | Run checks before commit |
| **commitlint** | Conventional commit messages |

---

*Performance is a feature. Measure before optimizing. Profile before guessing.*
