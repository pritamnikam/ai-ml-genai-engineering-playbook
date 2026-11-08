"""Offline lexical ranking and rank fusion helpers for the hybrid-search API."""

import math
import re
from collections import Counter
from collections.abc import Sequence


def tokenize(text: str) -> list[str]:
    """Lowercase text and split it into simple alphanumeric terms."""
    return re.findall(r"\w+", text.lower())


def bm25_rank(
    query: str,
    documents: Sequence[dict[str, str]],
    limit: int = 10,
    *,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[str]:
    """Rank document IDs with BM25; ties are broken by ID for repeatability.

    Query terms are unique so repeating a word in the query does not accidentally
    multiply its contribution; document term frequency still influences scores.
    """
    if limit < 0:
        raise ValueError("limit must not be negative")
    if k1 < 0 or not 0 <= b <= 1:
        raise ValueError("BM25 requires k1 >= 0 and b in [0, 1]")
    query_terms = set(tokenize(query))
    if not documents or not query_terms or limit == 0:
        return []

    tokenized = [tokenize(document["title"] + " " + document["content"]) for document in documents]
    lengths = [len(tokens) for tokens in tokenized]
    average_length = sum(lengths) / len(lengths) or 1.0
    document_frequencies: Counter[str] = Counter(
        term for tokens in tokenized for term in set(tokens)
    )
    scores: list[tuple[str, float]] = []

    for document, tokens, length in zip(documents, tokenized, lengths):
        frequencies = Counter(tokens)
        score = 0.0
        for term in query_terms:
            frequency = frequencies[term]
            if not frequency:
                continue
            df = document_frequencies[term]
            inverse_document_frequency = math.log(
                1 + (len(documents) - df + 0.5) / (df + 0.5)
            )
            denominator = frequency + k1 * (1 - b + b * length / average_length)
            score += (
                inverse_document_frequency
                * frequency
                * (k1 + 1)
                / denominator
            )
        scores.append((document["id"], score))

    # Stable tie-breaking makes results and tests repeatable across runs.
    scores.sort(key=lambda item: (-item[1], item[0]))
    return [document_id for document_id, score in scores if score > 0][:limit]


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[str]], *, k: int = 60
) -> list[tuple[str, float]]:
    """Fuse rankings using RRF and count each document once per source ranking.

    Deduplication prevents repeated IDs in a malformed or overlapping ranking
    from giving that source extra voting weight.
    """
    if k < 0:
        raise ValueError("k must not be negative")

    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, document_id in enumerate(dict.fromkeys(ranking), start=1):
            scores[document_id] = scores.get(document_id, 0.0) + 1 / (k + rank)

    # The ID tie-break keeps fused output deterministic when scores match.
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))
