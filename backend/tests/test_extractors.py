import pytest
from pathlib import Path
import tempfile
import pypdf
from app.pipelines.extractors import DocumentExtractor

def test_extract_markdown(tmp_path: Path):
    md_file = tmp_path / "sample_doc.md"
    md_file.write_text("# Deep Learning Architecture\n\nThis is an introduction to neural networks.", encoding="utf-8")

    doc = DocumentExtractor.extract_from_file(md_file)
    assert doc.title == "Deep Learning Architecture"
    assert "neural networks" in doc.content
    assert doc.source_type == "document"
    assert doc.metadata["format"] == "markdown"

def test_extract_text(tmp_path: Path):
    txt_file = tmp_path / "meeting_notes.txt"
    txt_file.write_text("Meeting Agenda for Sprint Planning\n1. Review completed tasks\n2. Plan Phase 2", encoding="utf-8")

    doc = DocumentExtractor.extract_from_file(txt_file)
    assert doc.title == "Meeting Agenda for Sprint Planning"
    assert "Sprint Planning" in doc.content
    assert doc.metadata["format"] == "txt"

def test_extract_pdf(tmp_path: Path):
    pdf_file = tmp_path / "test_document.pdf"
    
    # Generate minimal valid PDF using pypdf
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_metadata({"/Title": "Custom PDF Title", "/Author": "SMRITIX"})
    with open(pdf_file, "wb") as f:
        writer.write(f)

    doc = DocumentExtractor.extract_from_file(pdf_file)
    assert doc.title == "Custom PDF Title"
    assert doc.metadata["format"] == "pdf"
    assert doc.metadata["page_count"] == 1
