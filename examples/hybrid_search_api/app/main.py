"""FastAPI endpoints for transactional ingestion and hybrid document search."""

import hashlib
from contextlib import asynccontextmanager
from typing import Annotated
from urllib.parse import quote
from uuid import UUID, uuid4

import psycopg
from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from examples.hybrid_search_api.app.config import settings
from examples.hybrid_search_api.app.db import connect, ensure_schema
from examples.hybrid_search_api.app.embeddings import EmbeddingError, embed_text
from examples.hybrid_search_api.app.pdf_ingestion import (
    MAX_PDF_BYTES,
    PdfIngestionError,
    extract_pdf_chunks,
)
from examples.hybrid_search_api.app.retrieval import bm25_search, reciprocal_rank_fusion


class DocumentInput(BaseModel):
    """Validate and bound document fields before database writes."""

    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1, max_length=20_000)


class DocumentCreated(BaseModel):
    """Describe an accepted document and its asynchronous indexing status."""

    id: str
    status: str


class PdfIngested(BaseModel):
    """Report accepted PDF chunks and a URL for opening the retained source."""

    source_id: str
    source_name: str
    pages: int
    chunks: int
    source_url: str
    status: str


def qdrant_client() -> QdrantClient:
    """Create a Qdrant client using the process's configured endpoint."""
    return QdrantClient(url=settings.qdrant_url)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Ensure the vector collection exists, then release the startup client."""
    ensure_schema()
    client = qdrant_client()
    try:
        # Collection creation is guarded so restarting the API is idempotent.
        if not client.collection_exists(settings.qdrant_collection):
            client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=models.VectorParams(
                    size=settings.vector_size, distance=models.Distance.COSINE
                ),
            )
    finally:
        client.close()
    yield


app = FastAPI(
    title="Hybrid Search Playbook API",
    description=(
        "Page-cited PDF ingestion and hybrid BM25 + Ollama embedding search "
        "with PostgreSQL outbox indexing."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    """Check PostgreSQL availability and return an HTTP 503 when it is down."""
    try:
        with connect() as connection:
            connection.execute("SELECT 1")
    except psycopg.Error as error:
        raise HTTPException(status_code=503, detail="PostgreSQL is unavailable") from error
    return {"status": "ok"}


@app.post("/documents", response_model=DocumentCreated, status_code=202)
def create_document(document: DocumentInput) -> DocumentCreated:
    """Persist a document and its indexing event as one database transaction."""
    document_id = str(uuid4())
    payload = {
        "document_id": document_id,
        "title": document.title,
        "content": document.content,
    }
    try:
        with connect() as connection:
            # The connection context commits both inserts together or rolls both
            # back, so a saved document cannot lose its indexing request.
            connection.execute(
                "INSERT INTO documents (id, title, content) VALUES (%s, %s, %s)",
                (document_id, document.title, document.content),
            )
            connection.execute(
                """
                INSERT INTO outbox_events (event_type, aggregate_id, payload)
                VALUES ('document.upsert', %s, %s)
                """,
                (document_id, psycopg.types.json.Jsonb(payload)),
            )
    except psycopg.Error as error:
        raise HTTPException(status_code=503, detail="Could not save document") from error
    return DocumentCreated(id=document_id, status="accepted_for_indexing")


@app.post("/documents/pdf", response_model=PdfIngested, status_code=202)
async def upload_pdf(file: UploadFile = File(...)) -> PdfIngested:  # noqa: B008 - FastAPI field metadata
    """Extract a PDF into page-cited chunks and enqueue them atomically.

    The PDF bytes are bounded before parsing. Each chunk and its outbox event
    share one PostgreSQL transaction, so the worker can never index only a
    partially accepted upload.
    """
    try:
        data = await file.read(MAX_PDF_BYTES + 1)
    finally:
        await file.close()
    try:
        chunks = extract_pdf_chunks(data, file.filename or "uploaded-document.pdf")
    except PdfIngestionError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    source_id = str(uuid4())
    try:
        with connect() as connection:
            # Retain the bounded source PDF so citations can open the exact
            # evidence instead of pointing to an inaccessible client filename.
            connection.execute(
                """
                INSERT INTO pdf_sources (id, filename, content_sha256, pdf_bytes)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    source_id,
                    chunks[0].source_name,
                    hashlib.sha256(data).hexdigest(),
                    data,
                ),
            )
            for chunk in chunks:
                document_id = str(uuid4())
                title = f"{chunk.source_name} — page {chunk.page_number}"
                payload = {
                    "document_id": document_id,
                    "source_id": source_id,
                    "source_name": chunk.source_name,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "title": title,
                    "content": chunk.content,
                }
                connection.execute(
                    """
                    INSERT INTO documents
                        (id, title, content, source_id, source_name, page_number, chunk_index)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        document_id,
                        title,
                        chunk.content,
                        source_id,
                        chunk.source_name,
                        chunk.page_number,
                        chunk.chunk_index,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO outbox_events (event_type, aggregate_id, payload)
                    VALUES ('document.upsert', %s, %s)
                    """,
                    (document_id, psycopg.types.json.Jsonb(payload)),
                )
    except psycopg.Error as error:
        raise HTTPException(status_code=503, detail="Could not save PDF chunks") from error

    return PdfIngested(
        source_id=source_id,
        source_name=chunks[0].source_name,
        pages=len({chunk.page_number for chunk in chunks}),
        chunks=len(chunks),
        source_url=f"/documents/{source_id}/pdf",
        status="accepted_for_indexing",
    )


@app.get("/documents/{source_id}/pdf")
def get_pdf_source(source_id: UUID) -> Response:
    """Return a previously uploaded PDF so page citations resolve to evidence."""
    try:
        with connect() as connection:
            row = connection.execute(
                "SELECT filename, pdf_bytes FROM pdf_sources WHERE id = %s",
                (source_id,),
            ).fetchone()
    except psycopg.Error as error:
        raise HTTPException(status_code=503, detail="Could not read PDF source") from error
    if row is None:
        raise HTTPException(status_code=404, detail="PDF source not found")

    filename = quote(row["filename"], safe="")
    return Response(
        content=bytes(row["pdf_bytes"]),
        media_type="application/pdf",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f"inline; filename*=UTF-8''{filename}",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/search")
def search(
    q: Annotated[str, Query(min_length=1, max_length=500)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> dict[str, object]:
    """Return lexical/vector candidates fused into one ranked response."""
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id::text AS id, title, content, source_id::text AS source_id,
                   source_name, page_number, chunk_index
            FROM documents
            """
        ).fetchall()
    documents = [dict(row) for row in rows]
    # Resolve vector IDs only against authoritative PostgreSQL rows; this drops
    # stale vector points and ensures response content comes from the source DB.
    by_id = {document["id"]: document for document in documents}
    lexical_hits = bm25_search(q, documents, limit)
    lexical = [hit.document_id for hit in lexical_hits]
    lexical_scores = {hit.document_id: hit.score for hit in lexical_hits}

    semantic: list[str] = []
    client = qdrant_client()
    try:
        points = client.query_points(
            collection_name=settings.qdrant_collection,
            query=embed_text(q, purpose="query"),
            limit=limit,
        ).points
        semantic = [str(point.id) for point in points if str(point.id) in by_id]
    except (EmbeddingError, UnexpectedResponse, ResponseHandlingException) as error:
        raise HTTPException(status_code=503, detail="Semantic search service failed") from error
    finally:
        # Close per-request clients even when the vector query fails.
        client.close()

    fused = reciprocal_rank_fusion([lexical, semantic])[:limit]
    return {
        "query": q,
        "results": [
            {
                **by_id[document_id],
                "citation": (
                    f"{by_id[document_id]['source_name']}#page="
                    f"{by_id[document_id]['page_number']}"
                    if by_id[document_id].get("source_name")
                    and by_id[document_id].get("page_number")
                    else None
                ),
                "source_url": (
                    f"/documents/{by_id[document_id]['source_id']}/pdf"
                    f"#page={by_id[document_id]['page_number']}"
                    if by_id[document_id].get("source_id")
                    and by_id[document_id].get("page_number")
                    else None
                ),
                "bm25_score": lexical_scores.get(document_id),
                "semantic_rank": (
                    semantic.index(document_id) + 1 if document_id in semantic else None
                ),
                "rrf_score": score,
                "matched_by": [
                    source
                    for source, ranking in (("bm25", lexical), ("qdrant", semantic))
                    if document_id in ranking
                ],
            }
            for document_id, score in fused
        ],
    }
