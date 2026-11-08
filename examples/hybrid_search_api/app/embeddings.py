"""Provide deterministic hash vectors for exercising the local search pipeline.

These vectors make the example reproducible without downloading a model, but
they do not encode semantic similarity and must not be used as real embeddings.
"""

import hashlib
import math
import re


def demo_embedding(text: str, dimensions: int = 64) -> list[float]:
    """Return a normalized, deterministic signed-hash vector for local demos.

    SHA-256 avoids Python's process-randomized built-in hash, so indexing and
    querying the same token produce compatible vectors across restarts.
    """
    if dimensions < 1:
        raise ValueError("dimensions must be positive")

    vector = [0.0] * dimensions
    tokens = re.findall(r"\w+", text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        # Two digest bytes select a stable bucket and sign; collisions are an
        # accepted trade-off for this small, dependency-free wiring example.
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude:
        # Unit length makes cosine-distance comparisons independent of text length.
        vector = [value / magnitude for value in vector]
    return vector
