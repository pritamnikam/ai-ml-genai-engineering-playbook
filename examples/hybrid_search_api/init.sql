CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 300),
    content TEXT NOT NULL CHECK (length(content) BETWEEN 1 AND 20000),
    source_id UUID,
    source_name TEXT,
    page_number INTEGER,
    chunk_index INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS documents_source_chunk
    ON documents (source_id, chunk_index)
    WHERE source_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS pdf_sources (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    pdf_bytes BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS outbox_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'processed')),
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    claimed_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ,
    last_error TEXT
);

CREATE INDEX IF NOT EXISTS outbox_pending_order
    ON outbox_events (created_at, id)
    WHERE status IN ('pending', 'processing');

CREATE INDEX IF NOT EXISTS outbox_retry_schedule
    ON outbox_events (available_at, created_at, id)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS documents_search
    ON documents USING GIN (
        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, ''))
    );
