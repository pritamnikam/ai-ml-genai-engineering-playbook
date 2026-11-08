import logging
import time
from uuid import UUID

from qdrant_client import QdrantClient, models

from examples.hybrid_search_api.app.config import settings
from examples.hybrid_search_api.app.db import connect
from examples.hybrid_search_api.app.embeddings import demo_embedding
from examples.hybrid_search_api.app.main import qdrant_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_collection(client: QdrantClient) -> None:
    if not client.collection_exists(settings.qdrant_collection):
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(
                size=settings.vector_size, distance=models.Distance.COSINE
            ),
        )


def claim_one() -> tuple[str, dict[str, str]] | None:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT id::text AS id, payload
            FROM outbox_events
            WHERE status = 'pending'
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


def process_one(client: QdrantClient) -> bool:
    event = claim_one()
    if event is None:
        return False
    event_id, payload = event
    document_id = payload["document_id"]
    client.upsert(
        collection_name=settings.qdrant_collection,
        wait=True,
        points=[
            models.PointStruct(
                id=UUID(document_id),
                vector=demo_embedding(
                    payload["title"] + " " + payload["content"], settings.vector_size
                ),
                payload={
                    "document_id": document_id,
                    "title": payload["title"],
                },
            )
        ],
    )
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
    client = qdrant_client()
    try:
        ensure_collection(client)
        logger.info("Outbox worker started")
        while True:
            if not process_one(client):
                time.sleep(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
