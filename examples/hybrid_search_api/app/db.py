"""Create PostgreSQL connections with dictionary-shaped result rows."""

import psycopg
from psycopg.rows import dict_row

from examples.hybrid_search_api.app.config import settings


def connect() -> psycopg.Connection:
    """Open a configured connection; callers own its transaction and lifetime."""
    return psycopg.connect(settings.database_url, row_factory=dict_row)


def ensure_schema() -> None:
    """Apply additive schema changes needed by fresh and existing demo volumes.

    Compose's init scripts run only when PostgreSQL initializes an empty data
    directory; these idempotent ALTER statements let existing local volumes
    gain PDF provenance fields without dropping the learner's stored documents.
    """
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pdf_sources (
                id UUID PRIMARY KEY,
                filename TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                pdf_bytes BYTEA NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            ALTER TABLE documents
                ADD COLUMN IF NOT EXISTS source_id UUID,
                ADD COLUMN IF NOT EXISTS source_name TEXT,
                ADD COLUMN IF NOT EXISTS page_number INTEGER,
                ADD COLUMN IF NOT EXISTS chunk_index INTEGER
            """
        )
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS documents_source_chunk
            ON documents (source_id, chunk_index)
            WHERE source_id IS NOT NULL
            """
        )
        connection.execute(
            """
            ALTER TABLE outbox_events
            ADD COLUMN IF NOT EXISTS available_at TIMESTAMPTZ NOT NULL DEFAULT now()
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS outbox_retry_schedule
            ON outbox_events (available_at, created_at, id)
            WHERE status = 'pending'
            """
        )
