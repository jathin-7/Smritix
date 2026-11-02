# SMRITIX — Security & Privacy Architecture

> Document 02 of the SMRITIX Technical Blueprint

---

## 1. Security Principles

| Principle | Implementation |
|-----------|---------------|
| **Defense in depth** | Multiple layers: network, application, data, OS |
| **Least privilege** | Every component gets minimum required access |
| **Zero trust internally** | All inter-service calls authenticated |
| **Data minimization** | Only collect what's needed, delete when asked |
| **Secure defaults** | Everything locked down by default, user opts in |

---

## 2. Authentication Architecture

### 2.1 JWT-Based Auth (V1)

```
Login Request
    │
    ▼
┌───────────────────┐
│ Validate           │
│ email + password   │
│ (bcrypt verify)    │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐     ┌───────────────────┐
│ Issue JWT pair     │     │ Access Token      │
│                    │────▶│ • 15 min TTL      │
│                    │     │ • user_id claim    │
│                    │     │ • HS256 signed     │
│                    │     └───────────────────┘
│                    │     ┌───────────────────┐
│                    │────▶│ Refresh Token     │
│                    │     │ • 7 day TTL       │
│                    │     │ • Stored in DB    │
│                    │     │ • httpOnly cookie  │
└───────────────────┘     └───────────────────┘
```

### Token Storage (Critical Decision)

| Location | Used For | Security |
|----------|----------|----------|
| **httpOnly cookie** | Refresh token | Cannot be read by JavaScript (XSS-proof) |
| **Memory (JS variable)** | Access token | Lost on page refresh, but short-lived |
| ~~localStorage~~ | ~~Never~~ | ~~Vulnerable to XSS~~ |

### Token Refresh Flow

```
Access token expires → Frontend interceptor catches 401
    │
    ▼
POST /api/v1/auth/refresh  (refresh token sent via httpOnly cookie)
    │
    ▼
Backend validates refresh token → Issues new access token
    │
    ▼
Frontend retries original request with new access token
```

### 2.2 API Key Auth (V1.5+)

For programmatic access (browser extensions, integrations):

```sql
api_keys:
  key_hash    TEXT      -- bcrypt hash of the API key (never store plaintext)
  permissions JSONB     -- { "memories": ["read", "write"], "search": ["read"] }
  expires_at  TIMESTAMP
  last_used   TIMESTAMP
```

- API key sent via `Authorization: Bearer smx_...` header
- Key prefix `smx_` for easy identification
- Rate limited per key
- Scoped permissions

### 2.3 V1 Single-User Mode

V1 supports a simplified single-user setup:
- First user to register becomes admin
- Registration can be disabled after first user
- Environment variable `SMRITIX_SINGLE_USER=true`

---

## 3. Authorization & Access Control

### 3.1 Row-Level Security (RLS)

Every query is scoped to the authenticated user. PostgreSQL RLS as the last line of defense:

```sql
-- Every data table has RLS enabled
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON memories
  USING (user_id = current_setting('app.current_user_id')::UUID);
```

**Why RLS in addition to application-level checks:**
- Defense in depth — even if service layer has a bug, DB blocks cross-user access
- Works for raw SQL queries, migrations, debugging tools
- Database is the single source of truth for access control

### 3.2 Application-Level Authorization

```python
# Every service method receives the authenticated user
class MemoryService:
    async def get_memory(self, user_id: UUID, memory_id: UUID) -> Memory:
        memory = await self.repo.get(memory_id)
        if memory.user_id != user_id:
            raise ForbiddenError("Access denied")
        return memory
```

### 3.3 Permission Model

V1 permission levels (simple):

| Role | Capabilities |
|------|-------------|
| `owner` | Full CRUD on own data |

V2 permission levels (multi-user):

| Role | Capabilities |
|------|-------------|
| `owner` | Full CRUD, share, admin |
| `viewer` | Read-only access to shared memories |
| `editor` | Read + write on shared memories |

---

## 4. Privacy Architecture

### 4.1 User-Controlled Data Access

SMRITIX only accesses data the user explicitly provides:

```
┌─────────────────────────────────┐
│        User's Digital Life       │
│  ┌─────┐ ┌─────┐ ┌─────┐       │
│  │Notes│ │Code │ │Docs │ ...    │
│  └──┬──┘ └──┬──┘ └──┬──┘       │
│     │       │       │           │
│     ▼       ▼       ▼           │
│  ┌──────────────────────┐       │
│  │  User Consent Gate   │       │
│  │  (explicit upload    │       │
│  │   or API approval)   │       │
│  └──────────┬───────────┘       │
└─────────────┼───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│         SMRITIX Memory          │
│  (only approved data enters)    │
└─────────────────────────────────┘
```

### 4.2 Privacy Settings

User-configurable privacy controls:

```json
{
  "privacy": {
    "ai_provider": "local",           // "local" | "cloud"
    "cloud_ai_consent": false,         // explicit consent for cloud AI
    "auto_capture_enabled": false,     // V2: browser extension
    "data_retention_days": null,       // null = forever, or N days
    "search_history_enabled": true,
    "analytics_enabled": false,        // no telemetry by default
    "export_enabled": true             // user can always export their data
  }
}
```

### 4.3 Data Residency

| Version | Data Location |
|---------|--------------|
| V1 | All data on local machine (Docker volumes) |
| V2 | Optional cloud deployment (user chooses region) |
| Self-hosted | Always user-controlled |

### 4.4 AI Provider Privacy

```
┌────────────────────────────────────────────────┐
│              AI Provider Decision              │
│                                                │
│  User setting: ai_provider = ?                 │
│                                                │
│  ┌──────────────┐    ┌──────────────────────┐  │
│  │   "local"     │    │     "cloud"          │  │
│  │               │    │                      │  │
│  │ Data stays    │    │ Data sent to cloud   │  │
│  │ on machine.   │    │ provider API.        │  │
│  │ Ollama,       │    │ User must consent.   │  │
│  │ Whisper,      │    │ Content logged with  │  │
│  │ local embed.  │    │ provider's policy.   │  │
│  └──────────────┘    └──────────────────────┘  │
└────────────────────────────────────────────────┘
```

When using cloud providers:
- Show clear warning to user
- Require explicit consent toggle
- Log which data was sent to cloud (for user transparency)
- Never send more context than needed

### 4.5 Right to Delete

Hard delete cascade:

```
DELETE memory →
  ├── Delete memory_chunks (PostgreSQL)
  ├── Delete embeddings (Qdrant, by memory_id filter)
  ├── Delete knowledge_edges (source or target)
  ├── Delete memory_tags
  ├── Delete memory_sources
  ├── Delete from memory_access_log
  └── Delete uploaded source files (filesystem)
```

Soft delete (default) → Hard delete available via settings.

### 4.6 Data Export

Users can export all their data at any time:

```
GET /api/v1/settings/export → ZIP file containing:
  ├── memories.json         (all memories with metadata)
  ├── tags.json
  ├── projects.json
  ├── connections.json      (knowledge graph edges)
  ├── conversations.json    (ask SMRITIX history)
  ├── sources/              (uploaded documents)
  └── manifest.json         (export metadata, schema version)
```

---

## 5. Data Security

### 5.1 Encryption

| Layer | V1 | V2 |
|-------|----|----|
| **In transit** | HTTPS (TLS 1.3) via reverse proxy | Same |
| **At rest (DB)** | PostgreSQL native encryption (if enabled) | Full disk encryption |
| **At rest (files)** | OS-level file permissions | Encrypted file storage |
| **At rest (vectors)** | Qdrant volume permissions | Encrypted Qdrant storage |
| **Passwords** | bcrypt (cost factor 12) | Same |
| **API keys** | SHA-256 hash | Same |

### 5.2 Input Validation

All inputs validated at two layers:

```
Layer 1: Pydantic model validation (request parsing)
  ├── Type checking
  ├── Length limits (title: 500 chars, content: 1MB)
  ├── Format validation (email, UUID)
  └── Enum validation

Layer 2: Business logic validation (service layer)
  ├── Ownership verification
  ├── Duplicate detection (content_hash)
  ├── File type verification (magic bytes, not just extension)
  └── Size limits (file upload: 50MB max)
```

### 5.3 SQL Injection Prevention

- **SQLAlchemy ORM** — parameterized queries by default
- **No raw SQL** in application code (use ORM or text() with bind params)
- **RLS** as additional guard

### 5.4 XSS Prevention

- **React** — auto-escapes by default
- **Content Security Policy** headers
- **httpOnly cookies** — tokens not accessible to JS
- **Sanitize** user content before rendering (DOMPurify for rich text)

### 5.5 CSRF Protection

- **SameSite=Strict** on cookies
- **Origin header** validation
- **CSRF token** for state-changing requests via cookies

### 5.6 Rate Limiting

```python
# Per-endpoint rate limits
rate_limits = {
    "auth/login":       "5/minute",     # Brute force protection
    "auth/register":    "3/hour",       # Abuse prevention
    "memories":         "100/minute",   # Normal usage
    "search":           "60/minute",    # Prevent abuse
    "ask":              "20/minute",    # LLM cost control
    "ingest":           "10/minute",    # Resource intensive
    "voice/transcribe": "10/minute",    # Resource intensive
}
```

Implementation: Redis-backed sliding window (V1: slowapi library).

---

## 6. Security Headers

```python
# Applied via FastAPI middleware
security_headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "0",  # Rely on CSP instead
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(self), geolocation=()",
}
```

---

## 7. Threat Model (STRIDE)

| Threat | Category | Mitigation |
|--------|----------|------------|
| Attacker reads another user's memories | Spoofing / Info Disclosure | JWT auth + RLS + service-layer ownership checks |
| Brute force login | Spoofing | Rate limiting, account lockout after 10 failures |
| Malicious file upload | Tampering | File type verification (magic bytes), size limits, sandboxed processing |
| XSS via memory content | Tampering | React auto-escape, DOMPurify, CSP |
| SQL injection | Tampering | SQLAlchemy ORM, parameterized queries |
| Data exfiltration via AI provider | Info Disclosure | Local-first default, consent gate for cloud AI |
| Denial of service via large ingestion | Denial of Service | File size limits, ingestion queue with concurrency limits |
| Token theft | Elevation of Privilege | Short-lived access tokens, httpOnly refresh tokens, token rotation |
| Dependency vulnerability | All | Dependabot, regular updates, minimal dependencies |

---

## 8. Secrets Management

### V1 (Local Development)

```bash
# .env (never committed to git)
DATABASE_URL=postgresql+asyncpg://smritix:password@localhost:5432/smritix
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=<generated-256-bit-key>
JWT_ALGORITHM=HS256
OLLAMA_BASE_URL=http://localhost:11434
```

### V2+ (Production)

- Cloud secret manager (e.g., GCP Secret Manager, AWS Secrets Manager, HashiCorp Vault)
- Secrets injected as environment variables at runtime
- Never stored in code or config files
- Rotated regularly

---

## 9. Audit Logging

### What's Logged

```python
audit_events = [
    "user.login",
    "user.logout",
    "user.register",
    "memory.create",
    "memory.delete",
    "memory.access",
    "search.query",
    "ask.question",
    "ingest.start",
    "ingest.complete",
    "settings.change",
    "privacy.change",
    "export.request",
    "api_key.create",
    "api_key.revoke",
]
```

### What's NOT Logged

- Memory content (privacy)
- Search query text (privacy, unless user enables search history)
- AI prompts/responses (privacy)

### Log Storage

- V1: Application logs (structured JSON, stdout)
- V2: Dedicated audit log table or external log service

---

*Security is not a feature — it's a property of every feature. Every new feature must pass through this security model before implementation.*
