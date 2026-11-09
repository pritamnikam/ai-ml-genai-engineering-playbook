"""Deliver PostgreSQL outbox events to Qdrant with leased, retryable claims."""

import logging
import time
from uuid import UUID

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from examples.hybrid_search_api.app.config import settings
from examples.hybrid_search_api.app.db import connect
from examples.hybrid_search_api.app.embeddings import EmbeddingError, embed_text
from examples.hybrid_search_api.app.main import qdrant_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_collection(client: QdrantClient) -> None:
    """Create the configured Qdrant collection if the worker starts first."""
    # The existence check makes repeated worker starts safe for an existing collection.
    if not client.collection_exists(settings.qdrant_collection):
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(
                size=settings.vector_size, distance=models.Distance.COSINE
            ),
        )


def claim_one() -> tuple[str, dict[str, str]] | None:
    """Claim the oldest pending or expired event in a short DB transaction.

    ``SKIP LOCKED`` lets multiple workers claim different rows concurrently;
    the one-minute lease makes an abandoned claim eligible for another attempt.
    """
    with connect() as connection:
        row = connection.execute(
            """
            SELECT id::text AS id, payload
            FROM outbox_events
            WHERE (status = 'pending' AND available_at <= now())
               OR (status = 'processing' AND claimed_at < now() - interval '1 minute')
            ORDER BY created_at, id
            LIMIT 1
            FOR UPDATE SKIP LOCKED
            """
        ).fetchone()
        if row is None:
            return None
        connection.execute(
            """
            UPDATE outbox_events
            SET status = 'processing', claimed_at = now(), attempts = attempts + 1
            WHERE id = %s
            """,
            (row["id"],),
        )
        return row["id"], row["payload"]


def schedule_retry(event_id: str, error: Exception) -> None:
    """Return a failed event to pending with bounded exponential backoff."""
    with connect() as connection:
        connection.execute(
            """
            UPDATE outbox_events
            SET status = 'pending',
                claimed_at = NULL,
                available_at = now() + make_interval(
                    secs => LEAST(300, power(2, LEAST(attempts, 8))::integer)
                ),
                last_error = %s
            WHERE id = %s
            """,
            (str(error)[:2000], event_id),
        )


def process_one(client: QdrantClient) -> bool:
    """Index one claimed event and mark it complete only after Qdrant succeeds."""
    event = claim_one()
    if event is None:
        return False
    event_id, payload = event
    document_id = payload["document_id"]
    # PostgreSQL and Qdrant cannot share a transaction. Upsert first, then mark
    # processed: a crash can cause a duplicate, so the stable document UUID makes
    # the retry idempotent instead of risking a lost index update.
    try:
        vector = embed_text(payload["title"] + "\n" + payload["content"], purpose="document")
        client.upsert(
            collection_name=settings.qdrant_collection,
            wait=True,
            points=[
                models.PointStruct(
                    id=UUID(document_id),
                    vector=vector,
                    payload={
                        "document_id": document_id,
                        "source_id": payload.get("source_id"),
                        "source_name": payload.get("source_name"),
                        "page_number": payload.get("page_number"),
                        "chunk_index": payload.get("chunk_index"),
                        "title": payload["title"],
                    },
                )
            ],
        )
    except (EmbeddingError, UnexpectedResponse, ResponseHandlingException) as error:
        schedule_retry(event_id, error)
        logger.warning("Indexing event %s failed; retry scheduled: %s", event_id, error)
        return False
    with connect() as connection:
        connection.execute(
            """
            UPDATE outbox_events
            SET status = 'processed', processed_at = now(), last_error = NULL
            WHERE id = %s
            """,
            (event_id,),
        )
    logger.info("Indexed document %s from event %s", document_id, event_id)
    return True


def main() -> None:
    """Run the worker continuously, polling when no event is currently ready."""
    client = qdrant_client()
    try:
        ensure_collection(client)
        logger.info("Outbox worker started")
        while True:
            if not process_one(client):
                # Avoid a busy loop while keeping the demo worker simple.
                time.sleep(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
