from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.models.stream import PredictionMessage
from backend.app.services.session_service import SessionLimitError, SessionService


@pytest.mark.parametrize("ready, status", [(False, 503), (True, 200)])
def test_readiness_tracks_the_predictor(monkeypatch, ready, status):
    monkeypatch.setattr(
        "backend.app.api.routes.health.get_inference_service",
        lambda: SimpleNamespace(ready=ready),
    )
    assert TestClient(create_app()).get("/api/ready").status_code == status


def test_history_is_bounded_and_csv_does_not_write_to_disk(monkeypatch, tmp_path):
    service = SessionService(tmp_path)
    monkeypatch.setattr(service, "MAX_ACTIVE", 1)
    monkeypatch.setattr(service, "MAX_COMPLETED", 1)
    monkeypatch.setattr(service, "MAX_EVENTS", 1)
    monkeypatch.setattr("backend.app.api.routes.sessions.get_session_service", lambda: service)

    for session in ("first", "second"):
        service.start(session)
        with pytest.raises(SessionLimitError):
            service.start("extra")
        prediction = PredictionMessage(
            session_id=session, window_start=0, window_end=5, primary_class="rain",
            primary_confidence=0.6, env_tags=[], latency_ms=2,
            emotion=None, noise_intensity=None, engagement_score=None, attention_heatmap=None,
        )
        service.append_prediction(prediction)
        service.append_prediction(prediction)
        service.finish(session)

    client = TestClient(create_app())
    assert client.get("/api/sessions").json() == {"sessions": ["second"]}
    assert client.get("/api/sessions/first/export.csv").status_code == 404
    response = client.get("/api/sessions/second/export.csv")
    assert response.status_code == 200
    assert len(response.text.splitlines()) == 2
    assert list(tmp_path.iterdir()) == []
