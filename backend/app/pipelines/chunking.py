from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any

@dataclass
class TextChunk:
    chunk_index: int
    content: str
    token_count: int
    metadata: dict[str, Any] = field(default_factory=dict)

class RecursiveCharacterChunker:
    """
    Recursively splits text on natural boundaries (paragraphs, lines, sentences, words)
    to achieve the target chunk size with overlap, preserving structural meaning.
    """
    def __init__(
        self,
        chunk_size: int = 800,       # ~200-250 tokens
        chunk_overlap: int = 100,    # ~25-30 tokens
        separators: list[str] | None = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",
            "\n",
            ". ",
            "! ",
            "? ",
            "; ",
            " ",
            ""
        ]

    @staticmethod
    def estimate_tokens(text: str) -> int:
        # Standard fast heuristic: 1 token ~ 4 characters in English
        return max(1, len(text.split()))

    def split_text(self, text: str, metadata: dict[str, Any] | None = None) -> list[TextChunk]:
        cleaned = text.strip()
        if not cleaned:
            return []

        raw_chunks = self._recursive_split(cleaned, self.separators)
        merged_chunks = self._merge_splits(raw_chunks)

        meta = metadata or {}
        chunks: list[TextChunk] = []
        for idx, chunk_text in enumerate(merged_chunks):
            chunk_clean = chunk_text.strip()
            if chunk_clean:
                chunks.append(
                    TextChunk(
                        chunk_index=idx,
                        content=chunk_clean,
                        token_count=self.estimate_tokens(chunk_clean),
                        metadata=meta.copy()
                    )
                )
        return chunks

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]

        if not separators:
            # Base case: split by character limit
            return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

        sep = separators[0]
        remaining_seps = separators[1:]

        if sep == "":
            splits = list(text)
        elif sep in text:
            splits = text.split(sep)
        else:
            return self._recursive_split(text, remaining_seps)

        result: list[str] = []
        for i, split in enumerate(splits):
            piece = split
            # Reattach separator if not empty and not last piece
            if sep != "" and i < len(splits) - 1:
                piece += sep

            if len(piece) <= self.chunk_size:
                result.append(piece)
            else:
                result.extend(self._recursive_split(piece, remaining_seps))
        return result

    def _merge_splits(self, splits: list[str]) -> list[str]:
        merged: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for piece in splits:
            piece_len = len(piece)
            if current_len + piece_len > self.chunk_size and current_chunk:
                combined = "".join(current_chunk)
                merged.append(combined)

                # Keep overlap from the end of current_chunk
                overlap_accum: list[str] = []
                overlap_len = 0
                for item in reversed(current_chunk):
                    if overlap_len + len(item) <= self.chunk_overlap:
                        overlap_accum.insert(0, item)
                        overlap_len += len(item)
                    else:
                        break
                current_chunk = overlap_accum
                current_len = overlap_len

            current_chunk.append(piece)
            current_len += piece_len

        if current_chunk:
            merged.append("".join(current_chunk))

        return merged
