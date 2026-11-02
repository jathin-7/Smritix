from __future__ import annotations
import math
import hashlib
from typing import AsyncIterator
from app.ai.interfaces import LLMProvider, EmbeddingProvider, CompletionResult

class LocalDeterministicEmbeddingProvider(EmbeddingProvider):
    """
    Zero-dependency deterministic embedding provider.
    Generates 384-dimensional unit-normalized embeddings from text hashing and word frequencies.
    Guarantees that Phase 2 ingestion and vector storage run reliably without requiring an external GPU/Ollama instance.
    """
    def __init__(self, dimensions: int = 384):
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            words = text.lower().replace(",", " ").replace(".", " ").replace("!", " ").replace("?", " ").split()
            vec = [0.0] * self._dimensions
            for word in words:
                if not word:
                    continue
                h1 = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
                h2 = int(hashlib.sha1(word.encode("utf-8")).hexdigest(), 16)
                idx = h1 % self._dimensions
                sign = 1.0 if (h2 % 2 == 0) else -1.0
                vec[idx] += sign

            # L2 normalize
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            normalized = [v / norm for v in vec]
            results.append(normalized)
        return results

class LocalFallbackLLMProvider(LLMProvider):
    """Fallback LLM provider when external Ollama instance is not available."""
    
    def _generate_rag_response(self, prompt: str) -> str:
        import re
        lower_prompt = prompt.lower()
        if "context:" in lower_prompt and "question:" in lower_prompt:
            # Extract question
            q_part = prompt.split("Question:")[-1].strip()
            # Extract context
            ctx_part = prompt.split("Question:")[0]
            if "Context:" in ctx_part:
                ctx_part = ctx_part.split("Context:")[-1].strip()

            source_blocks = re.findall(r'(\[(\d+)\].*?)(?=\[\d+\]|$)', ctx_part, flags=re.DOTALL)
            
            if not source_blocks or "no relevant memories" in ctx_part.lower():
                return "I searched your memories, but couldn't find any relevant notes or documents to answer that question."

            q_words = set(re.findall(r'\w+', q_part.lower())) - {
                "what", "is", "the", "are", "we", "for", "in", "to", "how", "a", "an",
                "do", "does", "did", "can", "tell", "me", "about", "which", "where"
            }

            matched_points: list[str] = []
            for block_text, idx in source_blocks:
                lines = [l.strip() for l in block_text.strip().split("\n") if l.strip()]
                content_lines = [l for l in lines if not l.startswith("[") and not l.lower().startswith("title:")]
                candidate_text = " ".join(content_lines) if content_lines else " ".join(lines)
                
                sentences = re.split(r'(?<=[.!?])\s+', candidate_text)
                best_sentence = None
                best_score = 0
                for s in sentences:
                    s_clean = s.strip()
                    if not s_clean:
                        continue
                    s_words = set(re.findall(r'\w+', s_clean.lower()))
                    overlap = len(q_words & s_words)
                    if overlap > best_score:
                        best_score = overlap
                        best_sentence = s_clean

                if not best_sentence and sentences:
                    best_sentence = sentences[0]

                if best_sentence:
                    matched_points.append(f"[{idx}] {best_sentence.strip()}")

            if matched_points:
                first = matched_points[0]
                if not first.endswith("."):
                    first += "."
                more = (" Furthermore, " + " ".join(matched_points[1:2])) if len(matched_points) > 1 else ""
                return f"Based on your saved memories, {first}{more}"
            else:
                return "I searched your memories, but couldn't find any relevant details to answer your question."

        # Default fallback summary
        words = prompt.split()
        summary = " ".join(words[:min(len(words), 40)]) + "..."
        return f"Summary: {summary}"

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> CompletionResult:
        response_text = self._generate_rag_response(prompt)
        words = response_text.split()
        return CompletionResult(
            content=response_text,
            model="local-fallback",
            token_count=len(words),
            finish_reason="stop"
        )

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncIterator[str]:
        response_text = self._generate_rag_response(prompt)
        words = response_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
