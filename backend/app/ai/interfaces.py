from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Any

@dataclass
class CompletionResult:
    content: str
    model: str
    token_count: int | None = None
    finish_reason: str = "stop"
    raw_response: dict[str, Any] = field(default_factory=dict)

class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> CompletionResult:
        """Generate a complete text response."""
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncIterator[str]:
        """Stream generated text chunks."""
        pass

class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a list of texts."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the vector dimensionality."""
        pass
