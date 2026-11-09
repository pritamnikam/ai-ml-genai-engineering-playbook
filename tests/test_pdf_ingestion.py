"""Verify PDF extraction limits, overlapping chunks, and page provenance."""

import pytest

from examples.hybrid_search_api.app import pdf_ingestion
from examples.hybrid_search_api.app.pdf_ingestion import (
    PdfIngestionError,
    chunk_page_text,
    extract_pdf_chunks,
    safe_filename,
)


def test_chunk_page_text_overlaps_and_preserves_page_source() -> None:
    words = [f"word{index}" for index in range(500)]
    chunks = chunk_page_text(
        " ".join(words),
        source_name="guide.pdf",
        page_number=3,
        first_chunk_index=7,
    )

    assert len(chunks) == 2
    assert chunks[0].page_number == chunks[1].page_number == 3
    assert chunks[0].source_name == "guide.pdf"
    assert chunks[0].chunk_index == 7
    assert chunks[1].chunk_index == 8
    assert "word399" in chunks[0].content
    assert "word340" in chunks[1].content


def test_chunk_page_text_bounds_long_unbroken_tokens() -> None:
    chunks = chunk_page_text(
        "x" * 20_000,
        source_name="large.pdf",
        page_number=1,
        first_chunk_index=0,
    )
    assert len(chunks) > 1
    assert all(len(chunk.content) <= pdf_ingestion.MAX_CHUNK_CHARACTERS for chunk in chunks)


def test_safe_filename_discards_paths_and_control_characters() -> None:
    assert safe_filename("..\\private\\guide\\\x00x.pdf") == "x.pdf"


def test_extract_pdf_chunks_keeps_one_based_source_pages(monkeypatch) -> None:
    class FakePage:
        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

    class FakeReader:
        def __init__(self, *_args, **_kwargs):
            self.is_encrypted = False
            self.pages = [FakePage(""), FakePage("policy text on page two")]

    monkeypatch.setattr(pdf_ingestion, "PdfReader", FakeReader)
    chunks = extract_pdf_chunks(b"%PDF-1.7 test", r"C:\uploads\policy.pdf")

    assert len(chunks) == 1
    assert chunks[0].source_name == "policy.pdf"
    assert chunks[0].page_number == 2
    assert chunks[0].chunk_index == 0


def test_extract_pdf_chunks_rejects_non_pdf_and_encrypted_files(monkeypatch) -> None:
    with pytest.raises(PdfIngestionError, match="PDF header"):
        extract_pdf_chunks(b"not a pdf", "text.txt")

    class EncryptedReader:
        def __init__(self, *_args, **_kwargs):
            self.is_encrypted = True
            self.pages = []

    monkeypatch.setattr(pdf_ingestion, "PdfReader", EncryptedReader)
    with pytest.raises(PdfIngestionError, match="Encrypted"):
        extract_pdf_chunks(b"%PDF-1.7 test", "locked.pdf")
