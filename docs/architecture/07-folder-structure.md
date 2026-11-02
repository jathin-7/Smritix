# Folder Structure

This document outlines the complete project folder structure for SMRITIX, encompassing both the frontend (Next.js) and backend (FastAPI) applications.

## Directory Layout

```text
smritix/
├── docs/
│   └── architecture/                  # Architecture Decision Records (ADRs) and design docs
├── frontend/                          # Next.js application
│   ├── src/
│   │   ├── app/                       # Next.js App Router pages
│   │   │   ├── (auth)/                # Authentication routes (login, register)
│   │   │   ├── (dashboard)/           # Main application routes
│   │   │   └── layout.tsx             # Root layout
│   │   ├── components/
│   │   │   ├── ui/                    # Shared UI primitives (Button, Input, Card, Modal)
│   │   │   ├── features/              # Feature-specific components
│   │   │   │   ├── memories/
│   │   │   │   ├── search/
│   │   │   │   ├── ask/
│   │   │   │   ├── graph/
│   │   │   │   ├── voice/
│   │   │   │   ├── dashboard/
│   │   │   │   └── projects/
│   │   │   └── layouts/               # Page layouts and wrappers
│   │   ├── hooks/                     # Custom React hooks
│   │   ├── lib/                       # Utilities, API client, constants
│   │   │   ├── api/                   # API client and type-safe fetchers
│   │   │   ├── utils/
│   │   │   └── constants.ts
│   │   ├── stores/                    # Zustand stores
│   │   ├── types/                     # TypeScript type definitions
│   │   └── styles/                    # Global styles
│   ├── public/                        # Static assets (images, fonts, favicons)
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
├── backend/                           # Python FastAPI application
│   ├── app/
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── config.py                  # Configuration (pydantic-settings)
│   │   ├── dependencies.py            # Shared dependencies (DB sessions, current user)
│   │   ├── routers/                   # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── memories.py
│   │   │   ├── search.py
│   │   │   ├── ask.py
│   │   │   ├── ingest.py
│   │   │   ├── projects.py
│   │   │   ├── tags.py
│   │   │   ├── graph.py
│   │   │   ├── voice.py
│   │   │   ├── dashboard.py
│   │   │   └── settings.py
│   │   ├── services/                  # Business logic layer
│   │   │   ├── memory_service.py
│   │   │   ├── search_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── ingestion_service.py
│   │   │   ├── graph_service.py
│   │   │   ├── voice_service.py
│   │   │   ├── auth_service.py
│   │   │   └── dashboard_service.py
│   │   ├── repositories/              # Database access layer
│   │   │   ├── memory_repository.py
│   │   │   ├── user_repository.py
│   │   │   ├── project_repository.py
│   │   │   ├── graph_repository.py
│   │   │   └── base.py
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── memory.py
│   │   │   ├── project.py
│   │   │   ├── graph.py
│   │   │   ├── conversation.py
│   │   │   └── base.py
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   │   ├── memory.py
│   │   │   ├── search.py
│   │   │   ├── ask.py
│   │   │   ├── auth.py
│   │   │   ├── ingest.py
│   │   │   └── common.py
│   │   ├── ai/                        # AI abstraction layer
│   │   │   ├── base.py                # Abstract provider interfaces
│   │   │   ├── registry.py            # Provider registry
│   │   │   ├── providers/             # Implementations (Ollama, OpenAI, Anthropic, etc.)
│   │   │   │   ├── ollama.py
│   │   │   │   ├── openai.py
│   │   │   │   ├── anthropic.py
│   │   │   │   ├── local_embeddings.py
│   │   │   │   ├── whisper.py
│   │   │   │   └── piper.py
│   │   │   └── config.py
│   │   ├── pipelines/                 # Data processing pipelines
│   │   │   ├── ingestion.py           # Pipeline for new inputs
│   │   │   ├── chunking.py            # Document splitting strategies
│   │   │   ├── embedding.py           # Vectorization logic
│   │   │   ├── connection_discovery.py# Knowledge graph edge detection
│   │   │   └── code_ingestion.py      # Codebase parsing logic
│   │   ├── core/                      # Core utilities
│   │   │   ├── security.py            # JWT, password hashing
│   │   │   ├── exceptions.py          # Custom exception handlers
│   │   │   ├── middleware.py          # CORS, rate limiting
│   │   │   └── events.py              # Application lifecycle events
│   │   └── db/                        # Database configuration
│   │       ├── session.py
│   │       └── migrations/            # Alembic migrations
│   ├── tests/                         # Backend tests (pytest)
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── Dockerfile
├── infrastructure/                    # Deployment & infra
│   ├── docker/
│   │   ├── docker-compose.yml         # Local dev: FastAPI + Postgres + Qdrant + Ollama
│   │   ├── docker-compose.prod.yml
│   │   ├── Dockerfile.backend
│   │   └── Dockerfile.frontend
│   └── k8s/                           # Future Kubernetes manifests
├── scripts/                           # Dev and build scripts
│   ├── setup.sh
│   ├── seed.py
│   └── generate-types.sh
├── .env.example
├── .gitignore
├── README.md
└── Makefile                           # Task runner (e.g., make up, make migrate)
```

## Rationale for Key Structural Decisions

### Frontend `src/` Directory
Encapsulating application code in `src/` keeps configuration files (`tailwind.config.ts`, `next.config.ts`) at the root distinct from application logic. The separation of `components/ui` (reusable, dumb components) from `components/features` (domain-specific, smart components) prevents the UI folder from becoming a dumping ground and enforces clean boundaries.

### Backend Layered Architecture
The FastAPI backend follows a strict layered architecture:
- **Routers:** Handle HTTP requests and responses only.
- **Services:** Contain pure business logic and orchestrate actions.
- **Repositories:** Abstract database access.
- **Models vs. Schemas:** Clear separation between SQLAlchemy ORM models (`models/`) and Pydantic validation schemas (`schemas/`).
This separation of concerns makes testing easier and allows components (like the database engine) to be swapped with minimal friction.

### The AI Abstraction Layer (`backend/app/ai/`)
By creating an explicit AI abstraction layer with abstract base classes and a registry, the application is decoupled from any specific LLM provider. This allows SMRITIX to seamlessly switch between local models (Ollama) and cloud APIs (OpenAI, Anthropic) based on user preference or privacy constraints.

### Pipelines (`backend/app/pipelines/`)
Data ingestion and processing in a memory system is complex. The `pipelines` directory isolates chunking, embedding generation, and connection discovery logic away from standard API operations. These can eventually be moved to background workers (e.g., Celery) without rewriting the core logic.

### Infrastructure & Scripts
Keeping `infrastructure/` and `scripts/` at the root ensures that environment setup, local development via Docker Compose, and automated type generation are easily accessible to both frontend and backend engineers.
