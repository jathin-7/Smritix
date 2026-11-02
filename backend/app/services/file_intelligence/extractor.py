from __future__ import annotations
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import pypdf

@dataclass
class DocumentSection:
    page_number: int | None
    heading: str | None
    content: str

@dataclass
class ExtractedFileDocument:
    title: str
    file_name: str
    extension: str
    content: str
    sections: list[DocumentSection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    word_count: int = 0
    page_count: int = 0

SUPPORTED_EXTENSIONS = {
    # Documents
    ".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md", ".markdown", ".rtf",
    # Data & Config
    ".json", ".csv", ".tsv", ".yaml", ".yml", ".toml", ".xml", ".ini",
    # Source Code
    ".py", ".rs", ".ts", ".tsx", ".js", ".jsx", ".html", ".css", ".scss",
    ".sql", ".sh", ".bash", ".bat", ".ps1", ".c", ".cpp", ".h", ".hpp",
    ".go", ".java", ".kt", ".swift", ".rb", ".php"
}

class FileExtractionService:
    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB limit

    @classmethod
    def is_supported(cls, file_path: str | Path) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in SUPPORTED_EXTENSIONS

    @classmethod
    def extract(cls, file_path: str | Path) -> ExtractedFileDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        file_size = path.stat().st_size
        if file_size > cls.MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File exceeds maximum allowed size ({file_size} > {cls.MAX_FILE_SIZE_BYTES} bytes)")

        ext = path.suffix.lower()
        file_name = path.name

        try:
            if ext == ".pdf":
                return cls._extract_pdf(path, file_name, file_size)
            elif ext == ".docx":
                return cls._extract_docx(path, file_name, file_size)
            elif ext == ".pptx":
                return cls._extract_pptx(path, file_name, file_size)
            elif ext == ".xlsx":
                return cls._extract_xlsx(path, file_name, file_size)
            elif ext in [".md", ".markdown"]:
                return cls._extract_markdown(path, file_name, file_size)
            else:
                return cls._extract_text_or_code(path, file_name, ext, file_size)
        except Exception as e:
            # Fallback for plain text readable files or return descriptive error
            try:
                return cls._extract_text_or_code(path, file_name, ext, file_size)
            except Exception:
                raise RuntimeError(f"Failed to extract document contents from {file_name}: {str(e)}")

    @classmethod
    def _extract_pdf(cls, path: Path, file_name: str, file_size: int) -> ExtractedFileDocument:
        sections: list[DocumentSection] = []
        full_text_parts: list[str] = []
        doc_title: str | None = None
        author: str | None = None

        with open(path, "rb") as f:
            reader = pypdf.PdfReader(f)
            page_count = len(reader.pages)

            if reader.metadata:
                if reader.metadata.title:
                    doc_title = str(reader.metadata.title).strip()
                if reader.metadata.author:
                    author = str(reader.metadata.author).strip()

            for page_idx, page in enumerate(reader.pages):
                page_num = page_idx + 1
                try:
                    txt = page.extract_text() or ""
                except Exception:
                    txt = ""
                
                cleaned = txt.strip()
                if cleaned:
                    sections.append(DocumentSection(
                        page_number=page_num,
                        heading=f"Page {page_num}",
                        content=cleaned
                    ))
                    full_text_parts.append(cleaned)

        full_content = "\n\n".join(full_text_parts).strip()
        inferred_title = doc_title or path.stem.replace("_", " ").replace("-", " ").title()

        return ExtractedFileDocument(
            title=inferred_title,
            file_name=file_name,
            extension=".pdf",
            content=full_content,
            sections=sections,
            page_count=page_count,
            word_count=len(full_content.split()),
            metadata={
                "page_count": page_count,
                "author": author,
                "file_size": file_size,
                "format": "pdf"
            }
        )

    @classmethod
    def _extract_docx(cls, path: Path, file_name: str, file_size: int) -> ExtractedFileDocument:
        sections: list[DocumentSection] = []
        full_text_parts: list[str] = []
        current_heading: str | None = None
        current_section_lines: list[str] = []

        with zipfile.ZipFile(path, 'r') as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)

            namespaces = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            }

            for p in tree.iterfind('.//w:p', namespaces):
                texts = [node.text for node in p.iterfind('.//w:t', namespaces) if node.text]
                if not texts:
                    continue
                para_text = "".join(texts).strip()
                if not para_text:
                    continue

                # Check if paragraph has heading style
                pStyle = p.find('.//w:pStyle', namespaces)
                is_heading = False
                if pStyle is not None:
                    val = pStyle.get(f"{{{namespaces['w']}}}val", "")
                    if "Heading" in val or "heading" in val.lower():
                        is_heading = True

                if is_heading:
                    if current_section_lines:
                        sections.append(DocumentSection(
                            page_number=None,
                            heading=current_heading,
                            content="\n".join(current_section_lines)
                        ))
                        current_section_lines = []
                    current_heading = para_text
                else:
                    current_section_lines.append(para_text)

                full_text_parts.append(para_text)

        if current_section_lines:
            sections.append(DocumentSection(
                page_number=None,
                heading=current_heading,
                content="\n".join(current_section_lines)
            ))

        full_content = "\n\n".join(full_text_parts).strip()
        inferred_title = path.stem.replace("_", " ").replace("-", " ").title()

        return ExtractedFileDocument(
            title=inferred_title,
            file_name=file_name,
            extension=".docx",
            content=full_content,
            sections=sections,
            page_count=max(1, len(full_content.split()) // 350),
            word_count=len(full_content.split()),
            metadata={"format": "docx", "file_size": file_size}
        )

    @classmethod
    def _extract_pptx(cls, path: Path, file_name: str, file_size: int) -> ExtractedFileDocument:
        sections: list[DocumentSection] = []
        full_text_parts: list[str] = []

        with zipfile.ZipFile(path, 'r') as pptx:
            slide_names = sorted([name for name in pptx.namelist() if name.startswith('ppt/slides/slide') and name.endswith('.xml')])
            namespaces = {
                'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
            }

            for idx, slide_name in enumerate(slide_names):
                slide_num = idx + 1
                xml_content = pptx.read(slide_name)
                tree = ET.fromstring(xml_content)
                texts = [node.text for node in tree.iterfind('.//a:t', namespaces) if node.text]
                slide_text = "\n".join([t.strip() for t in texts if t.strip()])

                if slide_text:
                    sections.append(DocumentSection(
                        page_number=slide_num,
                        heading=f"Slide {slide_num}",
                        content=slide_text
                    ))
                    full_text_parts.append(f"--- Slide {slide_num} ---\n{slide_text}")

        full_content = "\n\n".join(full_text_parts).strip()
        return ExtractedFileDocument(
            title=path.stem.replace("_", " ").replace("-", " ").title(),
            file_name=file_name,
            extension=".pptx",
            content=full_content,
            sections=sections,
            page_count=len(sections),
            word_count=len(full_content.split()),
            metadata={"format": "pptx", "slide_count": len(sections), "file_size": file_size}
        )

    @classmethod
    def _extract_xlsx(cls, path: Path, file_name: str, file_size: int) -> ExtractedFileDocument:
        shared_strings: list[str] = []
        with zipfile.ZipFile(path, 'r') as xlsx:
            if 'xl/sharedStrings.xml' in xlsx.namelist():
                tree = ET.fromstring(xlsx.read('xl/sharedStrings.xml'))
                namespaces = {'': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                for t in tree.iterfind('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                    if t.text:
                        shared_strings.append(t.text.strip())

        full_content = "\n".join([s for s in shared_strings if s])
        return ExtractedFileDocument(
            title=path.stem.replace("_", " ").replace("-", " ").title(),
            file_name=file_name,
            extension=".xlsx",
            content=full_content,
            sections=[DocumentSection(page_number=1, heading="Spreadsheet Data", content=full_content)],
            page_count=1,
            word_count=len(full_content.split()),
            metadata={"format": "xlsx", "file_size": file_size}
        )

    @classmethod
    def _extract_markdown(cls, path: Path, file_name: str, file_size: int) -> ExtractedFileDocument:
        content = cls._read_text_safely(path)
        sections: list[DocumentSection] = []
        lines = content.splitlines()

        current_heading: str | None = None
        current_lines: list[str] = []
        doc_title: str | None = None

        for line in lines:
            s_line = line.strip()
            if s_line.startswith("# ") and not doc_title:
                doc_title = s_line[2:].strip()

            if s_line.startswith(("# ", "## ", "### ")):
                if current_lines:
                    sections.append(DocumentSection(
                        page_number=None,
                        heading=current_heading,
                        content="\n".join(current_lines)
                    ))
                    current_lines = []
                current_heading = s_line.lstrip("#").strip()
            else:
                current_lines.append(line)

        if current_lines:
            sections.append(DocumentSection(
                page_number=None,
                heading=current_heading,
                content="\n".join(current_lines)
            ))

        return ExtractedFileDocument(
            title=doc_title or path.stem.replace("_", " ").replace("-", " ").title(),
            file_name=file_name,
            extension=".md",
            content=content.strip(),
            sections=sections,
            page_count=max(1, len(content.split()) // 350),
            word_count=len(content.split()),
            metadata={"format": "markdown", "file_size": file_size}
        )

    @classmethod
    def _extract_text_or_code(cls, path: Path, file_name: str, ext: str, file_size: int) -> ExtractedFileDocument:
        content = cls._read_text_safely(path)
        return ExtractedFileDocument(
            title=path.stem.replace("_", " ").replace("-", " ").title(),
            file_name=file_name,
            extension=ext,
            content=content.strip(),
            sections=[DocumentSection(page_number=1, heading=file_name, content=content.strip())],
            page_count=max(1, len(content.split()) // 350),
            word_count=len(content.split()),
            metadata={"format": "text", "file_size": file_size}
        )

    @staticmethod
    def _read_text_safely(path: Path) -> str:
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                with open(path, "r", encoding=encoding, errors="replace") as f:
                    return f.read()
            except Exception:
                continue
        with open(path, "rb") as f:
            return f.read().decode("utf-8", errors="ignore")
