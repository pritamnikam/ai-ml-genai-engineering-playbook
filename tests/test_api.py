from types import SimpleNamespace

import psycopg
import pytest
from fastapi import HTTPException

from examples.hybrid_search_api.app import main


class FakeConnection:
    def __init__(self, rows=None):
        self.statements = []
        self.rows = rows or []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, parameters=None):
        self.statements.append((query, parameters))
        self.result = self.rows if "SELECT id::text AS id" in query else []
        return self

    def fetchall(self):
        return self.result


def test_create_document_writes_document_and_outbox_together(monkeypatch) -> None:
    connection = FakeConnection()
    monkeypatch.setattr(main, "connect", lambda: connection)

    created = main.create_document(
        main.DocumentInput(title="Reset", content="Reset a password.")
    )

    assert created.status == "accepted_for_indexing"
    assert len(connection.statements) == 2
    document_query, document_values = connection.statements[0]
    outbox_query, outbox_values = connection.statements[1]
    assert "INSERT INTO documents" in document_query
    assert "INSERT INTO outbox_events" in outbox_query
    assert document_values[0] == created.id == outbox_values[0]


def test_create_document_surfaces_database_failure(monkeypatch) -> None:
    def fail_connect():
        raise psycopg.OperationalError("database unavailable")

    monkeypatch.setattr(main, "connect", fail_connect)

    with pytest.raises(HTTPException) as error:
        main.create_document(main.DocumentInput(title="Reset", content="Details"))

    assert error.value.status_code == 503


def test_search_fuses_lexical_and_vector_results(monkeypatch) -> None:
    document_id = "00000000-0000-0000-0000-000000000001"
    connection = FakeConnection(
        [{"id": document_id, "title": "Password reset", "content": "Reset credentials."}]
    )

    class FakeQdrant:
        def query_points(self, **_kwargs):
            return SimpleNamespace(points=[SimpleNamespace(id=document_id)])

        def close(self):
            pass

    monkeypatch.setattr(main, "connect", lambda: connection)
    monkeypatch.setattr(main, "qdrant_client", FakeQdrant)

    response = main.search("password reset", 10)

    assert response["results"][0]["id"] == document_id
    assert response["results"][0]["matched_by"] == ["bm25", "qdrant"]
