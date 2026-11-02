from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from app.services.file_intelligence.extractor import ExtractedFileDocument, DocumentSection

@dataclass
class FileTextChunk:
    chunk_index: int
    content: str
    page_number: int | None = None
    section_heading: str | None = None
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

class FileChunkingService:
    def __init__(self, target_chunk_size: int = 800, overlap: int = 120):
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap

    def chunk_document(self, doc: ExtractedFileDocument) -> list[FileTextChunk]:
        chunks: list[FileTextChunk] = []
        global_index = 0

        # If document has distinct sections (pages or headings), chunk section-by-section
        if doc.sections:
            for section in doc.sections:
                section_chunks = self._chunk_text(
                    text=section.content,
                    page_number=section.page_number,
                    section_heading=section.heading,
                    start_index=global_index,
                    doc_meta=doc.metadata
                )
                chunks.extend(section_chunks)
                global_index += len(section_chunks)
        else:
            chunks = self._chunk_text(
                text=doc.content,
                page_number=1,
                section_heading=doc.title,
                start_index=0,
                doc_meta=doc.metadata
            )

        return chunks

    def _chunk_text(
        self,
        text: str,
        page_number: int | None,
        section_heading: str | None,
        start_index: int,
        doc_meta: dict[str, Any]
    ) -> list[FileTextChunk]:
        text = text.strip()
        if not text:
            return []

        # If text fits in a single chunk
        if len(text) <= self.target_chunk_size:
            return [
                FileTextChunk(
                    chunk_index=start_index,
                    content=text,
                    page_number=page_number,
                    section_heading=section_heading,
                    token_count=len(text.split()),
                    metadata={**doc_meta, "char_len": len(text)}
                )
            ]

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        result: list[FileTextChunk] = []
        current_chunk = ""
        current_idx = start_index

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= self.target_chunk_size:
                current_chunk = f"{current_chunk}\n\n{para}".strip() if current_chunk else para
            else:
                if current_chunk:
                    result.append(
                        FileTextChunk(
                            chunk_index=current_idx,
                            content=current_chunk,
                            page_number=page_number,
                            section_heading=section_heading,
                            token_count=len(current_chunk.split()),
                            metadata={**doc_meta, "char_len": len(current_chunk)}
                        )
                    )
                    current_idx += 1
                    # Sliding overlap
                    overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else ""
                    current_chunk = f"{overlap_text}\n{para}".strip()
                else:
                    # Paragraph is longer than target_chunk_size: slice into windows
                    start = 0
                    while start < len(para):
                        end = min(start + self.target_chunk_size, len(para))
                        slice_text = para[start:end].strip()
                        if slice_text:
                            result.append(
                                FileTextChunk(
                                    chunk_index=current_idx,
                                    content=slice_text,
                                    page_number=page_number,
                                    section_heading=section_heading,
                                    token_count=len(slice_text.split()),
                                    metadata={**doc_meta, "char_len": len(slice_text)}
                                )
                            )
                            current_idx += 1
                        start += self.target_chunk_size - self.overlap
                    current_chunk = ""

        if current_chunk:
            result.append(
                FileTextChunk(
                    chunk_index=current_idx,
                    content=current_chunk,
                    page_number=page_number,
                    section_heading=section_heading,
                    token_count=len(current_chunk.split()),
                    metadata={**doc_meta, "char_len": len(current_chunk)}
                )
            )

        return result
