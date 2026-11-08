import math

import pytest

from examples.hybrid_search_api.app.embeddings import demo_embedding
from examples.hybrid_search_api.app.retrieval import bm25_rank, reciprocal_rank_fusion


def test_bm25_prefers_matching_document() -> None:
    documents = [
        {"id": "a", "title": "Password reset", "content": "Reset an account password."},
        {"id": "b", "title": "Shipping", "content": "Track a delivery."},
    ]
    assert bm25_rank("password reset", documents) == ["a"]


def test_bm25_ties_are_stable_and_limit_is_respected() -> None:
    documents = [
        {"id": "b", "title": "Common term", "content": ""},
        {"id": "a", "title": "Common term", "content": ""},
    ]
    assert bm25_rank("common", documents, limit=1) == ["a"]


def test_bm25_validates_parameters() -> None:
    with pytest.raises(ValueError):
        bm25_rank("term", [], limit=-1)
    with pytest.raises(ValueError):
        bm25_rank("term", [], b=1.1)


def test_rrf_combines_rankings_and_counts_each_item_once_per_list() -> None:
    results = reciprocal_rank_fusion(
        [["a", "a", "b"], ["b", "a"]], k=0
    )
    assert results == [("a", 1.5), ("b", 1.5)]


def test_rrf_rejects_negative_offset() -> None:
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([["a"]], k=-1)


def test_demo_embedding_is_normalized_and_deterministic() -> None:
    first = demo_embedding("A small example")
    second = demo_embedding("A small example")
    assert first == second
    assert math.isclose(math.sqrt(sum(value**2 for value in first)), 1.0)


def test_demo_embedding_validates_dimensions() -> None:
    with pytest.raises(ValueError):
        demo_embedding("text", dimensions=0)
