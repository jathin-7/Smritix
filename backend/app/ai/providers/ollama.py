from __future__ import annotations
import json
from typing import AsyncIterator
import httpx
from app.ai.interfaces import LLMProvider, EmbeddingProvider, CompletionResult
from app.config import get_settings

settings = get_settings()

class OllamaLLMProvider(LLMProvider):
    def __init__(self, base_url: str | None = None, model: str = "llama3.2"):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> CompletionResult:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return CompletionResult(
                content=data.get("response", ""),
                model=self.model,
                token_count=data.get("eval_count"),
                finish_reason="stop" if data.get("done") else "length",
                raw_response=data
            )

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        chunk_data = json.loads(line)
                        yield chunk_data.get("response", "")

class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self, base_url: str | None = None, model: str = "nomic-embed-text", dimensions: int = 768):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Try batch /api/embed first (Ollama v0.1.34+)
            try:
                resp = await client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model, "input": texts}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    embeddings = data.get("embeddings", [])
                    if embeddings:
                        self._dimensions = len(embeddings[0])
                        return embeddings
            except Exception:
                pass

            # Fallback to single text /api/embeddings in sequence
            results = []
            for text in texts:
                resp = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text}
                )
                resp.raise_for_status()
                emb = resp.json().get("embedding", [])
                results.append(emb)
            if results and results[0]:
                self._dimensions = len(results[0])
            return results
