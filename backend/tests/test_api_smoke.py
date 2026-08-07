"""Router wiring smoke tests. These import the full app; run inside the backend
container (or an env with requirements installed). They exercise validation
paths that don't require Postgres/Redis/Chroma to be reachable."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_feedback_rejects_out_of_range_rating():
    # rating must be in [-1, 1]; 5 fails pydantic validation before any DB access.
    resp = client.post("/api/feedback", json={"message_id": 1, "rating": 5})
    assert resp.status_code == 422


def test_chat_requires_query():
    resp = client.post("/api/chat", json={"session_id": "test"})
    assert resp.status_code == 422


def test_tts_requires_text():
    resp = client.post("/api/tts", json={})
    assert resp.status_code == 400
