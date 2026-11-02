# 4. API Design & Backend Architecture

This document details the API design and backend architecture for SMRITIX, focusing on the Python + FastAPI implementation.

## 1. API Design Principles

The SMRITIX API adheres to the following core principles to ensure consistency, predictability, and ease of use:

- **RESTful Architecture:** The API is structured around resources, utilizing standard HTTP methods (GET, POST, PATCH, DELETE, PUT) with consistent resource naming (plural nouns).
- **JSON:API-Inspired Response Format:** Standardized response envelopes for data, metadata, and errors.
- **Pagination:** Cursor-based pagination is used for collections to ensure performance and consistency, particularly for frequently updated resources like memories or logs.
- **Rate Limiting:** API requests are rate-limited to prevent abuse and ensure service stability. Headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`) provide transparency.
- **API Versioning:** Versioning is handled via the URL path (e.g., `/api/v1/`) to allow for future non-backwards-compatible changes without disrupting existing clients.
- **OpenAPI/Swagger:** Comprehensive, automatically generated API documentation is available via OpenAPI (accessible at `/docs` or `/redoc`).

---

## 2. API Endpoints (V1 API Surface)

### 2.1 Auth
- `POST /api/v1/auth/register` — Register a new user
- `POST /api/v1/auth/login` — Authenticate and receive tokens
- `POST /api/v1/auth/refresh` — Refresh access token
- `POST /api/v1/auth/logout` — Invalidate tokens and log out
- `GET /api/v1/auth/me` — Retrieve current authenticated user profile

### 2.2 Memories
- `POST /api/v1/memories` — Create a new memory
- `GET /api/v1/memories` — List memories (paginated, filterable by type, tags, date range, project)
- `GET /api/v1/memories/{id}` — Get memory details, including chunks and sources
- `PATCH /api/v1/memories/{id}` — Update memory attributes
- `DELETE /api/v1/memories/{id}` — Soft delete a memory
- `POST /api/v1/memories/{id}/archive` — Archive a memory
- `POST /api/v1/memories/{id}/restore` — Restore a soft-deleted or archived memory
- `GET /api/v1/memories/{id}/connections` — Retrieve knowledge graph connections for the memory
- `GET /api/v1/memories/{id}/similar` — Find similar memories via vector search

### 2.3 Search
- `POST /api/v1/search` — Perform semantic search (query, filters, limit)
- `POST /api/v1/search/hybrid` — Perform combined semantic + full-text search
- `GET /api/v1/search/history` — Retrieve user's search history

### 2.4 Ask (RAG)
- `POST /api/v1/ask` — Ask a question and receive an AI-generated answer with source memories
- `POST /api/v1/ask/stream` — Streaming version of the ask endpoint via Server-Sent Events (SSE)
- `GET /api/v1/ask/conversations` — List past RAG conversations
- `GET /api/v1/ask/conversations/{id}` — Get a specific conversation with its messages

### 2.5 Ingestion
- `POST /api/v1/ingest/document` — Upload a document (PDF, markdown, text, etc.) for processing
- `POST /api/v1/ingest/url` — Ingest content from a provided URL
- `POST /api/v1/ingest/repository` — Ingest an entire code repository
- `GET /api/v1/ingest/jobs` — List ongoing and completed ingestion jobs
- `GET /api/v1/ingest/jobs/{id}` — Check the status of a specific job

### 2.6 Projects
- `POST /api/v1/projects` — Create a project
- `GET /api/v1/projects` — List projects
- `GET /api/v1/projects/{id}` — Get project details
- `PATCH /api/v1/projects/{id}` — Update a project
- `DELETE /api/v1/projects/{id}` — Delete a project
- `POST /api/v1/projects/{id}/memories` — Add a memory to a project
- `DELETE /api/v1/projects/{id}/memories/{memory_id}` — Remove a memory from a project

### 2.7 Tags
- `POST /api/v1/tags` — Create a tag
- `GET /api/v1/tags` — List tags
- `PATCH /api/v1/tags/{id}` — Update a tag
- `DELETE /api/v1/tags/{id}` — Delete a tag

### 2.8 Knowledge Graph
- `GET /api/v1/graph/connections?memory_id=X&depth=N` — Traverse connections from a specific node
- `GET /api/v1/graph/clusters` — Retrieve semantic clusters/topics
- `POST /api/v1/graph/edges` — Manually create an edge between two memories
- `DELETE /api/v1/graph/edges/{id}` — Remove an edge

### 2.9 Voice
- `POST /api/v1/voice/transcribe` — Upload audio to get a transcript
- `POST /api/v1/voice/synthesize` — Convert text to speech (returns audio stream)
- `WebSocket /api/v1/voice/stream` — Real-time bidirectional voice conversation

### 2.10 Dashboard
- `GET /api/v1/dashboard/stats` — Aggregate metrics: memory counts, types, recent activity
- `GET /api/v1/dashboard/timeline` — Chronological memory timeline
- `GET /api/v1/dashboard/knowledge-gaps` — Identified areas lacking information

### 2.11 Settings
- `GET /api/v1/settings` — Retrieve user settings
- `PATCH /api/v1/settings` — Update user settings
- `GET /api/v1/settings/privacy` — Retrieve privacy controls
- `PATCH /api/v1/settings/privacy` — Update privacy controls
- `GET /api/v1/settings/ai` — Retrieve AI provider configurations
- `PATCH /api/v1/settings/ai` — Update AI provider configurations

---

## 3. Request/Response Format

### 3.1 Standard Response Envelopes
Responses wrap data in a standard format:

**Success Response (e.g., Get Memory)**
```json
{
  "data": {
    "id": "mem_12345",
    "type": "memory",
    "attributes": {
      "content": "Discussed the new architecture for the semantic search engine...",
      "source_type": "note",
      "created_at": "2024-03-10T10:00:00Z",
      "tags": ["architecture", "search"]
    }
  },
  "meta": {
    "request_id": "req_abc123"
  }
}
```

**Paginated Collection (e.g., List Memories)**
```json
{
  "data": [
    {
      "id": "mem_12345",
      "type": "memory",
      "attributes": { ... }
    },
    {
      "id": "mem_12346",
      "type": "memory",
      "attributes": { ... }
    }
  ],
  "meta": {
    "pagination": {
      "next_cursor": "Y3JlYXRlZF9hdDoyMDI0LTAzLTEwVDEwOjAwOjAwWg==",
      "has_more": true
    }
  }
}
```

### 3.2 Specific Endpoint Examples

**Create Memory Request (`POST /api/v1/memories`)**
```json
{
  "content": "FastAPI uses Pydantic for data validation.",
  "source_type": "note",
  "tags": ["python", "fastapi"],
  "project_ids": ["proj_789"]
}
```

**Ask Question Request (`POST /api/v1/ask`)**
```json
{
  "query": "What framework are we using for data validation?",
  "conversation_id": "conv_456"
}
```

**Ask Question Response**
```json
{
  "data": {
    "answer": "We are using Pydantic for data validation within FastAPI.",
    "sources": [
      {
        "memory_id": "mem_12345",
        "snippet": "FastAPI uses Pydantic for data validation.",
        "relevance_score": 0.95
      }
    ]
  }
}
```

---

## 4. Backend Architecture

The backend is built with **Python and FastAPI**, leveraging asynchronous programming for high concurrency, especially important for I/O bound operations like LLM API calls and database queries.

### 4.1 Layered Architecture
The codebase strictly follows a layered architecture to ensure separation of concerns:

- **Router Layer (Controllers):** Defined using FastAPI `APIRouter`. Responsible for defining routes, handling HTTP requests, and executing request validation using Pydantic models. It delegates core logic to services.
- **Service Layer (Business Logic):** Contains the core application logic, orchestration of tasks (e.g., triggering the RAG pipeline), and cross-domain operations.
- **Repository Layer (Data Access):** Abstracts database interactions. Utilizes asynchronous SQLAlchemy for PostgreSQL, and specific clients for the vector database (e.g., Qdrant/Pinecone) and Knowledge Graph (e.g., Neo4j).
- **Infrastructure Layer:** Manages connections to external services: AI providers (OpenAI, Anthropic), Vector DBs, cloud file storage (S3), and message queues.

### 4.2 Key Backend Components
- **Dependency Injection:** Heavily utilizes FastAPI's `Depends()` for injecting services, repositories, and authentication contexts into routers, facilitating easy testing and modularity.
- **Background Tasks & Workers:**
  - **FastAPI BackgroundTasks:** Used for lightweight, immediate background jobs (e.g., sending a welcome email, minor logging).
  - **Celery:** Used for heavy, long-running asynchronous jobs like document ingestion pipelines, periodic knowledge graph clustering, and large data exports. Backed by Redis or RabbitMQ.
- **WebSocket Manager:** A dedicated connection manager handles active WebSocket connections for the real-time voice streaming (`/api/v1/voice/stream`), managing state, broadcasting, and connection lifecycle.
- **Event System:** An internal pub/sub or event bus mechanism triggers pipelines (e.g., `MemoryCreated` event triggers vector embedding generation and KG node creation).
- **Middleware:**
  - **CORS Middleware:** Configured for allowed origins (frontend).
  - **Rate Limiting Middleware:** Redis-backed rate limiter.
  - **Logging & Tracing Middleware:** Injects trace IDs and logs request/response metadata.
  - **Global Exception Handler Middleware:** Catches unhandled exceptions and formats them into standard API errors.

### 4.3 Authentication & Security
- **JWT-Based Authentication:** Employs JSON Web Tokens with short-lived access tokens and longer-lived refresh tokens.
- **Secure Token Storage:** Tokens are delivered to the frontend via `httpOnly`, `Secure`, `SameSite=Strict` cookies to mitigate XSS attacks. LocalStorage is not used for tokens.
- **API Keys:** For programmatic or third-party access, scoped API keys are supported.
- **Session Management:** Refresh tokens are tracked in the database to allow for explicit remote session revocation.

---

## 5. Error Handling

The API employs a consistent error response format to help clients easily parse and handle failures.

### Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The provided input data is invalid.",
    "details": [
      {
        "field": "content",
        "issue": "String should have at least 1 character."
      }
    ]
  },
  "meta": {
    "request_id": "req_abc123"
  }
}
```

### Error Codes Enumeration
- `UNAUTHORIZED`: Missing or invalid authentication credentials (401).
- `FORBIDDEN`: Authenticated but lacks required permissions (403).
- `NOT_FOUND`: The requested resource does not exist (404).
- `VALIDATION_ERROR`: Request data failed Pydantic validation (422).
- `RATE_LIMIT_EXCEEDED`: Too many requests (429).
- `CONFLICT`: Resource state conflict, e.g., duplicate tag name (409).
- `INTERNAL_SERVER_ERROR`: An unexpected backend failure (500).
- `EXTERNAL_SERVICE_ERROR`: A failure originating from an external dependency like an LLM provider (502/503).
