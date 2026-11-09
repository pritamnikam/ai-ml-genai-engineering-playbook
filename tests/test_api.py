"""Verify API transaction boundaries and hybrid-search response behavior."""

import asyncio
from types import SimpleNamespace
from uuid import UUID

import psycopg
import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from starlette.responses import Response

from examples.hybrid_search_api.app import main
from examples.hybrid_search_api.app.pdf_ingestion import PdfChunk


class FakeConnection:
    """Capture SQL issued by endpoints without requiring a live PostgreSQL server."""

    def __init__(self, rows=None):
        self.statements = []
        self.rows = rows or []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, parameters=None):
        self.statements.append((query, parameters))
        is_read = "SELECT id::text AS id" in query or "SELECT filename, pdf_bytes" in query
        self.result = self.rows if is_read else []
        return self

    def fetchall(self):
        return self.result

    def fetchone(self):
        return self.result[0] if self.result else None


def test_create_document_writes_document_and_outbox_together(monkeypatch) -> None:
    """Keep source data and the request to index it in the same transaction."""
    connection = FakeConnection()
    monkeypatch.setattr(main, "connect", lambda: connection)

    created = main.create_document(
        main.DocumentInput(title="Reset", content="Reset a password.")
    )

    assert created.status == "accepted_for_indexing"
    assert len(connection.statements) == 2
    document_query, document_values = connection.statements[0]
    outbox_query, outbox_values = connection.statements[1]
    assert "INSERT INTO documents" in document_query
    assert "INSERT INTO outbox_events" in outbox_query
    assert document_values[0] == created.id == outbox_values[0]


def test_create_document_surfaces_database_failure(monkeypatch) -> None:
    """Translate a database outage to an explicit service-unavailable response."""
    def fail_connect():
        raise psycopg.OperationalError("database unavailable")

    monkeypatch.setattr(main, "connect", fail_connect)

    with pytest.raises(HTTPException) as error:
        main.create_document(main.DocumentInput(title="Reset", content="Details"))

    assert error.value.status_code == 503


def test_search_fuses_lexical_and_vector_results(monkeypatch) -> None:
    """Include source attribution when BM25 and Qdrant find the same document."""
    document_id = "00000000-0000-0000-0000-000000000001"
    connection = FakeConnection(
        [
            {
                "id": document_id,
                "title": "policy.pdf — page 2",
                "content": "Reset credentials.",
                "source_id": "00000000-0000-0000-0000-000000000002",
                "source_name": "policy.pdf",
                "page_number": 2,
                "chunk_index": 0,
            }
        ]
    )

    class FakeQdrant:
        def query_points(self, **_kwargs):
            return SimpleNamespace(points=[SimpleNamespace(id=document_id)])

        def close(self):
            pass

    monkeypatch.setattr(main, "connect", lambda: connection)
    monkeypatch.setattr(main, "qdrant_client", FakeQdrant)
    monkeypatch.setattr(main, "embed_text", lambda *_args, **_kwargs: [0.1] * 768)

    response = main.search("password reset", 10)

    assert response["results"][0]["id"] == document_id
    assert response["results"][0]["matched_by"] == ["bm25", "qdrant"]
    assert response["results"][0]["citation"] == "policy.pdf#page=2"
    assert response["results"][0]["source_url"].endswith("#page=2")


def test_pdf_upload_writes_page_cited_chunks_and_outbox_events(monkeypatch) -> None:
    """Keep every chunk and its indexing event in the same source transaction."""
    connection = FakeConnection()
    chunks = [
        PdfChunk("First page text", "guide.pdf", 1, 0),
        PdfChunk("Second page text", "guide.pdf", 2, 1),
    ]
    monkeypatch.setattr(main, "connect", lambda: connection)
    monkeypatch.setattr(main, "extract_pdf_chunks", lambda *_args: chunks)

    async def upload():
        async with AsyncClient(
            transport=ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            return await client.post(
                "/documents/pdf",
                files={"file": ("guide.pdf", b"%PDF-1.7 demo", "application/pdf")},
            )

    response = asyncio.run(upload())
    assert response.status_code == 202
    result = response.json()

    assert result["pages"] == 2
    assert result["chunks"] == 2
    assert result["status"] == "accepted_for_indexing"
    assert len(connection.statements) == 5
    source_query, source_values = connection.statements[0]
    first_document_query, first_document_values = connection.statements[1]
    assert "INSERT INTO pdf_sources" in source_query
    assert source_values[0] == result["source_id"]
    assert "source_id, source_name, page_number, chunk_index" in first_document_query
    assert first_document_values[3:] == (result["source_id"], "guide.pdf", 1, 0)
    assert "INSERT INTO outbox_events" in connection.statements[2][0]
    assert "INSERT INTO outbox_events" in connection.statements[4][0]


def test_pdf_upload_rejects_non_pdf_content() -> None:
    """Reject invalid content before opening a database transaction."""

    async def upload():
        async with AsyncClient(
            transport=ASGITransport(app=main.app), base_url="http://test"
        ) as client:
            return await client.post(
                "/documents/pdf",
                files={"file": ("notes.txt", b"not a PDF", "text/plain")},
            )

    response = asyncio.run(upload())
    assert response.status_code == 422


def test_get_pdf_source_returns_pdf_inline_for_citations(monkeypatch) -> None:
    """Make page-fragment citations open the original uploaded source PDF."""
    pdf_bytes = b"%PDF-1.7 source"
    connection = FakeConnection(
        [{"filename": "policy guide.pdf", "pdf_bytes": pdf_bytes}]
    )
    monkeypatch.setattr(main, "connect", lambda: connection)

    response = main.get_pdf_source(UUID("00000000-0000-0000-0000-000000000001"))

    assert isinstance(response, Response)
    assert response.media_type == "application/pdf"
    assert response.body == pdf_bytes
    assert "filename*=UTF-8''policy%20guide.pdf" in response.headers["content-disposition"]
    assert response.headers["cache-control"] == "no-store"
