from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import pypdf

@dataclass
class ExtractedDocument:
    title: str
    content: str
    source_type: str
    metadata: dict[str, Any] = field(default_factory=dict)

class DocumentExtractor:
    @classmethod
    def extract_from_file(cls, file_path: str | Path, original_filename: str | None = None) -> ExtractedDocument:
        path = Path(file_path)
        filename = original_filename or path.name
        ext = path.suffix.lower()

        if ext == ".pdf":
            return cls._extract_pdf(path, filename)
        elif ext in [".md", ".markdown"]:
            return cls._extract_markdown(path, filename)
        else:
            # Default to text extractor (handles .txt, .py, .js, .ts, .json, .csv, etc.)
            return cls._extract_text(path, filename)

    @classmethod
    def _extract_pdf(cls, path: Path, filename: str) -> ExtractedDocument:
        pages_text: list[str] = []
        metadata: dict[str, Any] = {
            "filename": filename,
            "format": "pdf",
            "file_size": path.stat().st_size,
        }

        with open(path, "rb") as f:
            reader = pypdf.PdfReader(f)
            metadata["page_count"] = len(reader.pages)
            if reader.metadata:
                if reader.metadata.title:
                    metadata["doc_title"] = str(reader.metadata.title)
                if reader.metadata.author:
                    metadata["author"] = str(reader.metadata.author)

            for i, page in enumerate(reader.pages):
                txt = page.extract_text()
                if txt:
                    pages_text.append(txt)

        content = "\n\n".join(pages_text).strip()
        inferred_title = (
            metadata.get("doc_title")
            or Path(filename).stem.replace("_", " ").replace("-", " ").title()
        )

        return ExtractedDocument(
            title=inferred_title,
            content=content,
            source_type="document",
            metadata=metadata
        )

    @classmethod
    def _extract_markdown(cls, path: Path, filename: str) -> ExtractedDocument:
        raw_text = cls._read_file_text(path)
        lines = raw_text.splitlines()

        inferred_title = Path(filename).stem.replace("_", " ").replace("-", " ").title()
        for line in lines:
            line_s = line.strip()
            if line_s.startswith("# "):
                inferred_title = line_s[2:].strip()
                break

        return ExtractedDocument(
            title=inferred_title,
            content=raw_text.strip(),
            source_type="document",
            metadata={
                "filename": filename,
                "format": "markdown",
                "file_size": path.stat().st_size,
            }
        )

    @classmethod
    def _extract_text(cls, path: Path, filename: str) -> ExtractedDocument:
        raw_text = cls._read_file_text(path)
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        
        inferred_title = Path(filename).stem.replace("_", " ").replace("-", " ").title()
        if lines:
            first_line = lines[0][:80]
            # If first line looks like a title
            if len(first_line) > 3 and not first_line.startswith(("{", "[", "import", "//")):
                inferred_title = first_line

        return ExtractedDocument(
            title=inferred_title,
            content=raw_text.strip(),
            source_type="document",
            metadata={
                "filename": filename,
                "format": path.suffix.lstrip(".").lower() or "text",
                "file_size": path.stat().st_size,
            }
        )

    @staticmethod
    def _read_file_text(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="latin-1", errors="replace")
