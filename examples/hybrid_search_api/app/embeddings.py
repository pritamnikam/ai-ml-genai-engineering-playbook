"""Call the local Ollama embedding model for semantic indexing and retrieval."""

import json
import math
from urllib.error import URLError
from urllib.request import Request, urlopen

from examples.hybrid_search_api.app.config import settings


class EmbeddingError(RuntimeError):
    """Raised when the local embedding service cannot provide a valid vector."""


def embed_text(text: str, *, purpose: str) -> list[float]:
    """Create one configured-model embedding for a document chunk or query.

    Nomic Embed expects distinct task prefixes. Matching the document and query
    prefixes is important because the model was trained for asymmetric search.
    """
    if not text.strip():
        raise ValueError("text must not be empty")
    if purpose not in {"document", "query"}:
        raise ValueError("purpose must be 'document' or 'query'")

    prefix = "search_document: " if purpose == "document" else "search_query: "
    request_body = json.dumps(
        {
            "model": settings.embedding_model,
            "input": prefix + text,
            "truncate": False,
        }
    ).encode("utf-8")
    request = Request(
        settings.embedding_url,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.embedding_timeout_seconds) as response:
            result = json.load(response)
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise EmbeddingError("The local embedding service request failed") from error

    if not isinstance(result, dict):
        raise EmbeddingError("The embedding service returned an invalid response")
    embeddings = result.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != 1:
        raise EmbeddingError("The embedding service returned an invalid response")
    vector = embeddings[0]
    if (
        not isinstance(vector, list)
        or len(vector) != settings.vector_size
        or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in vector)
    ):
        raise EmbeddingError("The embedding service returned an invalid vector")
    return [float(value) for value in vector]
