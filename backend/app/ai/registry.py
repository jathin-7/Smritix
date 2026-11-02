from __future__ import annotations
import httpx
from app.ai.interfaces import LLMProvider, EmbeddingProvider
from app.ai.providers.ollama import OllamaLLMProvider, OllamaEmbeddingProvider
from app.ai.providers.local_fallback import LocalDeterministicEmbeddingProvider, LocalFallbackLLMProvider
from app.config import get_settings

settings = get_settings()

class ProviderRegistry:
    def __init__(self) -> None:
        self._llm_provider: LLMProvider | None = None
        self._embedding_provider: EmbeddingProvider | None = None

    async def is_ollama_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def get_llm_provider(self) -> LLMProvider:
        if self._llm_provider is not None:
            return self._llm_provider

        if await self.is_ollama_available():
            self._llm_provider = OllamaLLMProvider()
        else:
            self._llm_provider = LocalFallbackLLMProvider()
        return self._llm_provider

    async def get_embedding_provider(self) -> EmbeddingProvider:
        if self._embedding_provider is not None:
            return self._embedding_provider

        if await self.is_ollama_available():
            self._embedding_provider = OllamaEmbeddingProvider()
        else:
            self._embedding_provider = LocalDeterministicEmbeddingProvider()
        return self._embedding_provider

registry = ProviderRegistry()

async def get_embedding_provider() -> EmbeddingProvider:
    return await registry.get_embedding_provider()

async def get_llm_provider() -> LLMProvider:
    return await registry.get_llm_provider()
