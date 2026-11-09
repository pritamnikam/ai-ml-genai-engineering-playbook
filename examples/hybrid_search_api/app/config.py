"""Load immutable service settings from environment variables at process start.

The API and worker share these settings so they agree on database, collection,
and vector dimensions. Environment-based configuration also keeps credentials
and deployment-specific values out of the source tree.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Connection and indexing settings shared by the API and worker."""

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://playbook:playbook-local-demo-only@localhost:5432/playbook",
    )
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "playbook_pdf_chunks")
    vector_size: int = int(os.getenv("VECTOR_SIZE", "768"))
    embedding_url: str = os.getenv("EMBEDDING_URL", "http://localhost:11434/api/embed")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    embedding_timeout_seconds: float = float(os.getenv("EMBEDDING_TIMEOUT_SECONDS", "30"))


settings = Settings()
