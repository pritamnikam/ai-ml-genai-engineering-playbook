"""Verify that transient embedding outages leave outbox events retryable."""

from examples.hybrid_search_api import worker
from examples.hybrid_search_api.app.embeddings import EmbeddingError


def test_process_one_schedules_retry_when_embedding_service_is_unavailable(monkeypatch) -> None:
    event = (
        "7",
        {
            "document_id": "00000000-0000-0000-0000-000000000001",
            "title": "Policy page 1",
            "content": "Returns within 30 days.",
        },
    )
    scheduled = []

    def fail_embedding(*_args, **_kwargs):
        raise EmbeddingError("offline")

    monkeypatch.setattr(worker, "claim_one", lambda: event)
    monkeypatch.setattr(worker, "embed_text", fail_embedding)
    monkeypatch.setattr(
        worker,
        "schedule_retry",
        lambda event_id, error: scheduled.append((event_id, str(error))),
    )

    assert worker.process_one(object()) is False
    assert scheduled == [("7", "offline")]
