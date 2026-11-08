import hashlib
import math
import re


def demo_embedding(text: str, dimensions: int = 64) -> list[float]:
    """Return a deterministic signed-hash vector for local wiring demos only."""
    if dimensions < 1:
        raise ValueError("dimensions must be positive")

    vector = [0.0] * dimensions
    tokens = re.findall(r"\w+", text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude:
        vector = [value / magnitude for value in vector]
    return vector
