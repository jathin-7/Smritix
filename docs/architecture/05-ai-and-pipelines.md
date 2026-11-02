# 05 - AI and Pipelines Architecture

This document defines the AI Abstraction Layer, data ingestion pipelines, RAG architecture, and automatic memory mechanisms for SMRITIX — a Personal AI Memory System.

## 1. AI Abstraction Layer

To ensure future flexibility and prevent vendor lock-in, SMRITIX uses a provider-agnostic AI layer. The abstraction allows seamless switching between local models (Zero-Cost V1) and cloud providers.

### Provider Interfaces

The interfaces are defined using Python abstract base classes to guarantee uniform implementations across all integrations.

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, List

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 1000) -> CompletionResult:
        pass

    @abstractmethod
    async def stream(self, prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 1000) -> AsyncIterator[str]:
        pass

class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        pass

class STTProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, language: str = None) -> TranscriptResult:
        pass

class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, voice: str = None) -> AudioResult:
        pass
```

### Supported Providers

The system is designed for a phased rollout of providers.

| Capability | V1 (Zero-Cost) | V1.5 | V2 |
|-----------|----------------|------|----|
| LLM | Ollama (llama3, mistral) | + OpenAI, Anthropic, Google | + Custom fine-tuned |
| Embeddings | all-MiniLM-L6-v2 (local via sentence-transformers) | + OpenAI ada-002 | + Custom models |
| STT | Whisper (local via faster-whisper) | + Deepgram, Google | + Custom |
| TTS | Piper TTS (local) | + ElevenLabs, Google | + Custom |

### Provider Registry

The `ProviderRegistry` manages instantiation and execution logic:
- **Configuration-Driven:** Active providers are set in user settings (e.g., SQLite/JSON).
- **Fallback Chains:** Can configure fallback logic (e.g., attempt local `Ollama`, fallback to `OpenAI` if down).
- **Cost Tracking:** Cloud providers track token usage and estimated costs per query.
- **Model Configuration:** Users can tweak model parameters globally or per query.

---

## 2. Document Ingestion Pipeline

The document ingestion pipeline processes external files into indexed, searchable chunks within SMRITIX.

```text
Input → Extraction → Cleaning → Chunking → Embedding → Storage → Indexing → Connection Discovery
```

### Stage 1: Input Handling
- **Supported Formats:** PDF, Markdown, TXT, DOCX, HTML, EPUB, code files.
- **Validation:** File size limits, mime-type checking.
- **Storage:** Original files are uploaded and saved to a local file storage directory for reference.

### Stage 2: Content Extraction
- **PDF:** PyMuPDF (`fitz`) or `pdfplumber`.
- **DOCX:** `python-docx`.
- **HTML:** `BeautifulSoup` + `readability` for main content extraction.
- **Code:** `tree-sitter` for AST-aware structure parsing.
- **Markdown:** Direct text processing.

### Stage 3: Cleaning & Normalization
- Strip excessive whitespace and anomalous characters.
- Normalize unicode representation (NFC).
- Extract source metadata (title, author, creation date).
- Detect language using fastText or similar libraries.

### Stage 4: Chunking Strategy
- **Text Splitter:** Recursive character text splitter (LangChain-style approach).
- **Sizing:** `512` tokens per chunk (configurable), with a `50` token overlap to preserve context across boundaries.
- **Boundaries:** Respects paragraph and section (header) boundaries.
- **Code-Aware:** Uses `tree-sitter` to respect function and class boundaries, keeping logical units together.
- **Metadata Inheritance:** Each chunk inherits the metadata from its parent memory (Memory ID, title, author).

### Stage 5: Embedding Generation
- **Batching:** Chunks are sent to the `EmbeddingProvider` in batches to optimize throughput.
- **Rate Limiting:** Managed concurrency for cloud providers to prevent `429 Too Many Requests`.
- **Caching:** Uses a `content_hash` to skip re-embedding if the chunk text has not changed.

### Stage 6: Storage
- **Chunks:** Stored in the `memory_chunks` table in PostgreSQL.
- **Embeddings:** Pushed to Qdrant, using `memory_id` and `chunk_index` in the payload for back-referencing.
- **Source Tracking:** Original document references logged in the `memory_sources` table.

### Stage 7: Post-Processing
- **AI Summary:** `LLMProvider` generates a concise summary of the ingested document.
- **Auto-Tagging:** Extracts key themes as tags.
- **Connection Discovery:** Semantic search against Qdrant to find related existing memories, linking them via `knowledge_edges`.

---

## 3. Memory Creation Pipeline

User-initiated memory creation is streamlined for speed and immediate availability.

```text
User Input → Validation → Storage → Chunking → Embedding → Connection Discovery → Notification
```

- **Quick Capture:** Minimal processing. Captures title and content quickly (e.g., from a quick entry widget or shortcut).
- **Full Creation:** Includes title, content, custom tags, project associations, and external source URLs.
- **Auto-Capture:** Mechanisms like browser extensions or API endpoints pushing content automatically.
- Processes asynchronously so the UI remains responsive.

---

## 4. RAG (Retrieval-Augmented Generation) Architecture

The "Ask SMRITIX" feature employs a robust RAG pipeline to answer user questions using their personal knowledge base.

```text
User Question → Query Enhancement → Retrieval → Reranking → Context Assembly → LLM Gen → Source Attribution → Response
```

### Step 1: Query Enhancement
- **Expansion:** LLM generates search variants and synonyms based on the raw query.
- **Keyword Extraction:** Identifies critical terms for BM25/full-text search.
- **Intent Detection:** Determines if the query is factual, exploratory, or comparative to adjust retrieval strategies.

### Step 2: Retrieval (Hybrid)
- **Semantic Search:** Top-K dense retrieval via Qdrant using the query embedding.
- **Keyword Search:** Full-text search via PostgreSQL `tsvector`.
- **Graph Traversal:** Explores the knowledge graph for memories heavily connected to the retrieved nodes.
- **Merge:** Results are combined and deduplicated.

### Step 3: Reranking
- **V1:** Reciprocal Rank Fusion (RRF) to combine semantic and keyword scores.
- **V2:** Implementation of a cross-encoder model to re-score the top-N retrieved chunks against the original query for higher precision.

### Step 4: Context Assembly
- Filters down to the absolute top-N chunks post-reranking.
- Assembles a context window that respects the LLM's token limits.
- Includes source metadata (title, URL, chunk index) within the prompt for accurate attribution.

### Step 5: Generation
- Injects instructions into the system prompt to enforce source-aware answers (e.g., "Only use the provided context to answer").
- Passes context and the enhanced question to the `LLMProvider`.
- Streams the response back to the frontend via Server-Sent Events (SSE).

### Step 6: Source Attribution
- The LLM is prompted to include inline citations (e.g., `[1]`, `[2]`).
- The backend parses these citations, mapping them back to the original `memory_id` and chunk.
- Returns a structured response containing both the markdown text and a list of structured source citations.

---

## 5. Automatic Memory Architecture

SMRITIX actively organizes and enriches the knowledge base without manual intervention.

### Auto-Connection Discovery
- **On Creation:** When a new memory is created, it performs a vector search for the top 5 similar memories.
- **Thresholds:** If cosine similarity > `0.85`, it automatically creates a `similar_to` edge in the knowledge graph.
- **Batch Jobs:** A periodic job re-scans the corpus to identify new overarching connections as the knowledge base grows.

### Auto-Tagging
- The LLM analyzes the memory content and suggests appropriate tags.
- It prioritizes matching against the user's existing tag vocabulary.
- Tags can be auto-applied or placed in a "suggested" state for user confirmation.

### Auto-Summarization
- Generates a concise (1-2 sentence) summary for long-form memories.
- Triggers an update to the summary automatically if the memory is edited.

### Knowledge Gap Detection
- Analyzes the knowledge graph layout to find isolated clusters (orphan topics).
- Identifies overarching themes with sparse memory coverage.
- Suggests new areas for exploration based on existing patterns.

---

## 6. Code/Repository Ingestion

Allows users to ingest entire codebases as projects.

- **Scanning:** Clones or scans a local repository file tree.
- **Parsing:** Uses `tree-sitter` for deep understanding of code structures (Python, JS/TS, Rust, etc.).
- **Extraction:** Isolates functions, classes, docstrings, READMEs, and high-level comments.
- **Memory Creation:** Generates structured memories per logical unit (file, class, module).
- **Project Tracking:** Links all resulting memories to a single Project entity.

---

## 7. Voice Architecture

Integrating speech for hands-free interactions.

- **Voice Input Flow:** Voice Input → `STTProvider` → Transcript → Memory Creation Pipeline.
- **Voice Conversation Flow:** WebSocket Audio Stream → `STT` → RAG Pipeline → `TTS` → Audio Response to User.
- **Rollout Phases:**
  - **V1:** File upload transcription only (processing pre-recorded voice memos).
  - **V1.5:** Real-time streaming voice interface (walkie-talkie mode).
