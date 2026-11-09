"""Dependency-free BM25 full-text ranking and reciprocal-rank fusion helpers."""

import math
import re
from collections import Counter
from collections.abc import Sequence
from typing import NamedTuple
from unicodedata import normalize


def tokenize(text: str) -> list[str]:
    """Normalize Unicode and split text into case-insensitive word tokens.

    Unicode normalization makes visually equivalent text more likely to share
    terms; preserving digits keeps product IDs and error codes searchable.
    """
    return re.findall(r"[^\W_]+", normalize("NFKC", text).casefold())


class BM25Hit(NamedTuple):
    """A ranked document ID and its corpus-relative BM25 score."""

    document_id: str
    score: float


class BM25Index:
    """In-memory BM25 index with title weighting for small local corpora.

    The implementation uses only the Python standard library. The index is
    rebuilt from the supplied documents for each search request; that keeps the
    example simple but is not appropriate for large production corpora.
    """

    def __init__(
        self,
        documents: Sequence[dict[str, object]],
        *,
        k1: float = 1.5,
        b: float = 0.75,
        title_boost: float = 2.0,
    ) -> None:
        if k1 < 0 or not 0 <= b <= 1 or title_boost < 0:
            raise ValueError("BM25 requires k1 >= 0, b in [0, 1], and title_boost >= 0")

        self.documents = documents
        self.k1 = k1
        self.b = b
        self.title_boost = title_boost
        self.title_terms = [Counter(tokenize(str(document["title"]))) for document in documents]
        self.body_terms = [Counter(tokenize(str(document["content"]))) for document in documents]
        self.lengths = [
            sum(body.values()) + title_boost * sum(title.values())
            for title, body in zip(self.title_terms, self.body_terms)
        ]
        self.average_length = sum(self.lengths) / len(self.lengths) if documents else 0.0
        self.document_frequencies: Counter[str] = Counter(
            term
            for title, body in zip(self.title_terms, self.body_terms)
            for term in title.keys() | body.keys()
        )

    def search(self, query: str, limit: int = 10) -> list[BM25Hit]:
        """Return positive-scoring hits in deterministic descending score order."""
        if limit < 0:
            raise ValueError("limit must not be negative")
        query_terms = set(tokenize(query))
        if not self.documents or not query_terms or limit == 0:
            return []

        average_length = self.average_length or 1.0
        hits = []
        for document, title, body, length in zip(
            self.documents, self.title_terms, self.body_terms, self.lengths
        ):
            score = 0.0
            for term in query_terms:
                frequency = body[term] + self.title_boost * title[term]
                if not frequency:
                    continue
                document_frequency = self.document_frequencies[term]
                inverse_document_frequency = math.log(
                    1 + (len(self.documents) - document_frequency + 0.5)
                    / (document_frequency + 0.5)
                )
                normalization = self.k1 * (
                    1 - self.b + self.b * length / average_length
                )
                score += (
                    inverse_document_frequency
                    * frequency
                    * (self.k1 + 1)
                    / (frequency + normalization)
                )
            if score > 0:
                hits.append(BM25Hit(str(document["id"]), score))

        # Stable tie-breaking makes API results reproducible for equal scores.
        hits.sort(key=lambda hit: (-hit.score, hit.document_id))
        return hits[:limit]


def bm25_search(
    query: str,
    documents: Sequence[dict[str, object]],
    limit: int = 10,
    *,
    k1: float = 1.5,
    b: float = 0.75,
    title_boost: float = 2.0,
) -> list[BM25Hit]:
    """Build a standard-library index and return scored BM25 search hits."""
    return BM25Index(
        documents, k1=k1, b=b, title_boost=title_boost
    ).search(query, limit)


def bm25_rank(
    query: str,
    documents: Sequence[dict[str, object]],
    limit: int = 10,
    *,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[str]:
    """Return BM25-ranked IDs for callers that do not need individual scores."""
    return [hit.document_id for hit in bm25_search(query, documents, limit, k1=k1, b=b)]


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[str]], *, k: int = 60
) -> list[tuple[str, float]]:
    """Fuse ranked ID lists using standard RRF and deterministic tie-breaking.

    Deduplication prevents repeated IDs in a malformed or overlapping ranking
    from giving that source extra voting weight. The constant ``k`` smooths
    rank differences and makes RRF independent of each retriever's score scale.
    """
    if k < 0:
        raise ValueError("k must not be negative")

    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, document_id in enumerate(dict.fromkeys(ranking), start=1):
            scores[document_id] = scores.get(document_id, 0.0) + 1 / (k + rank)

    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))
