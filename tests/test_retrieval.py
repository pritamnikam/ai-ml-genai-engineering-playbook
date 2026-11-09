"""Check deterministic BM25 scoring and reciprocal-rank fusion behavior."""

import json
from io import BytesIO

import pytest

from examples.hybrid_search_api.app import embeddings as embeddings_module
from examples.hybrid_search_api.app.embeddings import EmbeddingError, embed_text
from examples.hybrid_search_api.app.retrieval import (
    BM25Index,
    bm25_rank,
    bm25_search,
    reciprocal_rank_fusion,
    tokenize,
)


def test_bm25_prefers_matching_document() -> None:
    documents = [
        {"id": "a", "title": "Password reset", "content": "Reset an account password."},
        {"id": "b", "title": "Shipping", "content": "Track a delivery."},
    ]
    assert bm25_rank("password reset", documents) == ["a"]


def test_bm25_returns_scores_and_boosts_title_matches() -> None:
    documents = [
        {"id": "body", "title": "General help", "content": "battery"},
        {"id": "title", "title": "Battery", "content": ""},
    ]
    hits = bm25_search("battery", documents, title_boost=3)
    assert hits[0].document_id == "title"
    assert hits[0].score > 0


def test_bm25_normalizes_unicode_and_preserves_identifiers() -> None:
    assert tokenize("ＣＡＦÉ E-1042") == ["café", "e", "1042"]


def test_bm25_ties_are_stable_and_limit_is_respected() -> None:
    documents = [
        {"id": "b", "title": "Common term", "content": ""},
        {"id": "a", "title": "Common term", "content": ""},
    ]
    assert bm25_rank("common", documents, limit=1) == ["a"]


def test_bm25_handles_empty_query_and_empty_corpus() -> None:
    assert bm25_search("  ", [{"id": "a", "title": "title", "content": "body"}]) == []
    assert BM25Index([]).search("query") == []


def test_bm25_validates_parameters() -> None:
    documents = [{"id": "a", "title": "title", "content": "body"}]
    with pytest.raises(ValueError):
        bm25_rank("term", [], limit=-1)
    with pytest.raises(ValueError):
        BM25Index(documents, b=1.1)
    with pytest.raises(ValueError):
        BM25Index(documents, title_boost=-1)


def test_rrf_combines_rankings_and_counts_each_item_once_per_list() -> None:
    results = reciprocal_rank_fusion(
        [["a", "a", "b"], ["b", "a"]], k=0
    )
    assert results == [("a", 1.5), ("b", 1.5)]


def test_rrf_rejects_negative_offset() -> None:
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([["a"]], k=-1)


def test_embed_text_uses_task_prefix_and_validates_dimension(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return BytesIO(json.dumps({"embeddings": [[0.25] * 768]}).encode())

    monkeypatch.setattr(embeddings_module, "urlopen", fake_urlopen)
    assert len(embed_text("page content", purpose="document")) == 768
    body = json.loads(captured["request"].data)
    assert body["input"] == "search_document: page content"
    assert body["truncate"] is False
    assert captured["timeout"] > 0

    embed_text("find return terms", purpose="query")
    query_body = json.loads(captured["request"].data)
    assert query_body["input"] == "search_query: find return terms"


def test_embed_text_rejects_invalid_service_vector(monkeypatch) -> None:
    monkeypatch.setattr(
        embeddings_module,
        "urlopen",
        lambda *_args, **_kwargs: BytesIO(b'{"embeddings":[[0.1]]}'),
    )
    with pytest.raises(EmbeddingError):
        embed_text("query", purpose="query")
