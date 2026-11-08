"""FastAPI endpoints for transactional ingestion and hybrid document search."""

from contextlib import asynccontextmanager
from typing import Annotated
from uuid import uuid4

import psycopg
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from examples.hybrid_search_api.app.config import settings
from examples.hybrid_search_api.app.db import connect
from examples.hybrid_search_api.app.embeddings import demo_embedding
from examples.hybrid_search_api.app.retrieval import bm25_rank, reciprocal_rank_fusion


class DocumentInput(BaseModel):
    """Validate and bound document fields before database writes."""

    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1, max_length=20_000)


class DocumentCreated(BaseModel):
    """Describe an accepted document and its asynchronous indexing status."""

    id: str
    status: str


def qdrant_client() -> QdrantClient:
    """Create a Qdrant client using the process's configured endpoint."""
    return QdrantClient(url=settings.qdrant_url)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Ensure the vector collection exists, then release the startup client."""
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
    description="Educational BM25 + Qdrant search with PostgreSQL outbox ingestion.",
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


@app.get("/search")
def search(
    q: Annotated[str, Query(min_length=1, max_length=500)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> dict[str, object]:
    """Return lexical/vector candidates fused into one ranked response."""
    with connect() as connection:
        rows = connection.execute(
            "SELECT id::text AS id, title, content FROM documents"
        ).fetchall()
    documents = [dict(row) for row in rows]
    # Resolve vector IDs only against authoritative PostgreSQL rows; this drops
    # stale vector points and ensures response content comes from the source DB.
    by_id = {document["id"]: document for document in documents}
    lexical = bm25_rank(q, documents, limit)

    semantic: list[str] = []
    client = qdrant_client()
    try:
        points = client.query_points(
            collection_name=settings.qdrant_collection,
            query=demo_embedding(q, settings.vector_size),
            limit=limit,
        ).points
        semantic = [str(point.id) for point in points if str(point.id) in by_id]
    except UnexpectedResponse as error:
        raise HTTPException(status_code=503, detail="Qdrant search failed") from error
    finally:
        # Close per-request clients even when the vector query fails.
        client.close()

    fused = reciprocal_rank_fusion([lexical, semantic])[:limit]
    return {
        "query": q,
        "results": [
            {
                **by_id[document_id],
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
