# Database & Data Architecture

## 1. Database Schema (PostgreSQL)

The primary datastore for SMRITIX is PostgreSQL. We utilize UUIDv7 for time-sortable primary keys, JSONB for flexible metadata, and Row-Level Security (RLS) for multi-tenant isolation. 

### Enums
```sql
CREATE TYPE memory_type_enum AS ENUM ('note', 'document', 'snippet', 'conversation', 'code', 'voice_transcript', 'web_clip', 'annotation');
CREATE TYPE source_type_enum AS ENUM ('manual', 'ingested', 'auto_captured', 'voice', 'api');
CREATE TYPE relation_type_enum AS ENUM ('references', 'similar_to', 'derived_from', 'contradicts', 'extends', 'part_of', 'related_to');
CREATE TYPE edge_created_by_enum AS ENUM ('user', 'ai', 'system');
CREATE TYPE role_enum AS ENUM ('user', 'assistant', 'system');
CREATE TYPE job_status_enum AS ENUM ('pending', 'processing', 'completed', 'failed');
```

### Core Tables

```sql
-- 1. Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access their own record" ON users FOR ALL USING (id = auth.uid());

-- 2. Memories
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(512),
    content TEXT,
    summary TEXT,
    memory_type memory_type_enum NOT NULL,
    source_type source_type_enum NOT NULL,
    source_uri VARCHAR(1024),
    source_metadata JSONB DEFAULT '{}'::jsonb,
    content_hash VARCHAR(255) NOT NULL,
    is_archived BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(summary, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(content, '')), 'C')
    ) STORED
);
CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_memories_content_hash ON memories(content_hash);
CREATE INDEX idx_memories_search ON memories USING GIN(search_vector);
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users access own memories" ON memories FOR ALL USING (user_id = auth.uid());

-- 3. Memory Chunks
CREATE TABLE memory_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    embedding_id VARCHAR(255), -- Reference to Qdrant point ID
    metadata JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX idx_memory_chunks_memory_id ON memory_chunks(memory_id);

-- 4. Tags & Memory Tags
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);
CREATE INDEX idx_tags_user_id ON tags(user_id);
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users access own tags" ON tags FOR ALL USING (user_id = auth.uid());

CREATE TABLE memory_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE(memory_id, tag_id)
);
CREATE INDEX idx_memory_tags_tag_id ON memory_tags(tag_id);

-- 5. Memory Sources
CREATE TABLE memory_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    source_type VARCHAR(255) NOT NULL,
    source_uri VARCHAR(1024),
    source_title VARCHAR(512),
    raw_content_hash VARCHAR(255),
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_memory_sources_memory_id ON memory_sources(memory_id);

-- 6. Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_projects_user_id ON projects(user_id);
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users access own projects" ON projects FOR ALL USING (user_id = auth.uid());

CREATE TABLE project_memories (
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    PRIMARY KEY (project_id, memory_id)
);

-- 7. Knowledge Edges
CREATE TABLE knowledge_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    target_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    relation_type relation_type_enum NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    created_by edge_created_by_enum NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_memory_id, target_memory_id, relation_type)
);
CREATE INDEX idx_knowledge_edges_user_id ON knowledge_edges(user_id);
CREATE INDEX idx_knowledge_edges_target ON knowledge_edges(target_memory_id);
ALTER TABLE knowledge_edges ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users access own knowledge edges" ON knowledge_edges FOR ALL USING (user_id = auth.uid());

-- 8. Conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(512),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users access own convos" ON conversations FOR ALL USING (user_id = auth.uid());

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role role_enum NOT NULL,
    content TEXT NOT NULL,
    source_memories UUID[], -- References to memory IDs utilized
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_conv_messages_conv_id ON conversation_messages(conversation_id);

-- 9. Voice Sessions
CREATE TABLE voice_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    audio_storage_path VARCHAR(1024),
    transcript TEXT,
    duration_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_voice_sessions_user_id ON voice_sessions(user_id);
ALTER TABLE voice_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users access own voice sessions" ON voice_sessions FOR ALL USING (user_id = auth.uid());

-- 10. Ingestion Jobs
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_type VARCHAR(255) NOT NULL,
    source_uri VARCHAR(1024),
    status job_status_enum NOT NULL DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX idx_ingestion_jobs_user_status ON ingestion_jobs(user_id, status);
ALTER TABLE ingestion_jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users access own jobs" ON ingestion_jobs FOR ALL USING (user_id = auth.uid());

-- 11. User Permissions
CREATE TABLE user_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID NOT NULL,
    permission_level VARCHAR(50) NOT NULL
);
CREATE INDEX idx_user_perms_user_id ON user_permissions(user_id);

-- 12. API Keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    permissions JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);

-- 13. Memory Access Log
CREATE TABLE memory_access_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    access_type VARCHAR(50) NOT NULL,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_memory_access_log_user_id ON memory_access_log(user_id);
CREATE INDEX idx_memory_access_log_memory_id ON memory_access_log(memory_id);

-- 14. Search History
CREATE TABLE search_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    result_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_search_history_user_id ON search_history(user_id);
```

## 2. Vector Database Architecture

SMRITIX relies on a robust vector storage layer to support semantic search.

*   **V1 Engine:** Qdrant (local, Docker-based). Chosen for production readiness, advanced filtering capabilities, and payload support. It avoids some of the limitations of Chroma at scale.
*   **Collection Design:** One global collection named `smritix_chunks` with a `user_id` payload filter. This ensures multi-tenant security without the overhead of creating individual collections per user.
*   **Embedding Dimensions:** 
    *   384 (all-MiniLM-L6-v2) for initial V1 deployment.
    *   Designed to be dimension-agnostic to easily transition to 1536 (OpenAI ada-002) or 768 (Cohere) in the future.
*   **Payload (Metadata):** Stored in Qdrant for pre-filtering:
    *   `user_id` (UUID) - crucial for multi-tenant isolation
    *   `memory_id` (UUID)
    *   `chunk_index` (int)
    *   `memory_type` (string)
    *   `tags` (list of strings)
    *   `created_at` (timestamp)
*   **Search Strategy:** Hybrid Search.
    *   **Dense:** Cosine similarity on embeddings.
    *   **Sparse/Lexical:** BM25 via Qdrant's sparse vectors or utilizing PostgreSQL `tsvector` alongside dense retrieval.
*   **Reranking:** Pipeline includes a placeholder for cross-encoder reranking (e.g., `bge-reranker-base`) to score combined hybrid search results before returning top K to the LLM.

## 3. Knowledge Graph Architecture

The knowledge graph models explicit and implicit relationships between memories.

*   **V1 Architecture:** Built on top of PostgreSQL using the `knowledge_edges` table. Graph traversals are performed using recursive Common Table Expressions (CTEs). 
    *   **Node:** A `Memory` record.
    *   **Edge:** A `knowledge_edge` record, capturing typed relationships (`relation_type`) and a `confidence` score.
*   **V1.5 Architecture (Planned):** Optional Neo4j integration via an adapter pattern. The system will sync `memories` and `knowledge_edges` to a Neo4j graph database for advanced analytics and visualization if configured.
*   **Graph Queries Supported (via SQL Recursive CTEs):**
    *   Find connections N hops away (e.g., retrieving related context for RAG).
    *   Identify isolated clusters of thought.
    *   Discover bridging concepts between disparate topics.
*   **Automatic Edge Creation:** Background tasks process new memories via AI. The LLM extracts entities and similarities, emitting `relation_type` events that system ingestors use to create edges labeled with `created_by = 'ai'` and assigned a confidence score.

## 4. Data Migration Strategy

*   **Migration Tool:** Alembic will be used to manage and version PostgreSQL schema changes in the Python/FastAPI environment.
*   **Versioning:** All schema modifications will be represented as sequential Alembic migration scripts, ensuring repeatable deployments across environments.
*   **Seed Data:** A `seed.py` script will provide foundational data for development, inserting default tags, sample users, and a set of test memories demonstrating various types and edges.
