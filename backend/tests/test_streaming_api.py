import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.app.main import create_app
from backend.app.services.inference_service import InferenceService
from backend.app.services.session_service import SessionService


class FixedPredictor:
    def predict(self, samples):
        assert len(samples) == 80000
        return "rain", 0.6


def test_websocket_sends_status_when_checkpoint_missing(monkeypatch):
    monkeypatch.delenv("SONICAID_ESC10_MODEL", raising=False)
    client = TestClient(create_app())
    with client.websocket_connect("/ws/stream") as ws:
        assert ws.receive_json()["status"] == "model_unavailable"
        with pytest.raises(WebSocketDisconnect) as error:
            ws.receive_json()
        assert error.value.code == 1013


def test_websocket_stream_uses_real_predictor_after_full_window(monkeypatch, tmp_path):
    service = InferenceService(SessionService(tmp_path), predictor=FixedPredictor())
    monkeypatch.setattr(
        "backend.app.api.routes.stream.get_inference_service", lambda: service
    )
    client = TestClient(create_app())
    with client.websocket_connect("/ws/stream") as ws:
        status = ws.receive_json()
        assert status["status"] == "ready"
        assert status["model"] == "ESC-10"
        for _ in range(5):
            ws.send_bytes(b"\x00\x00" * 16000)
        result = ws.receive_json()
        assert result["primary_class"] == "rain"
        assert result["primary_confidence"] == pytest.approx(0.6)
        assert result["engagement_score"] is None


def test_websocket_blocks_unknown_browser_origin(monkeypatch):
    monkeypatch.setenv("SONICAID_ALLOWED_ORIGINS", "http://localhost:5173")
    client = TestClient(create_app())
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            "/ws/stream", headers={"origin": "https://malicious.example"}
        ):
            pass


def test_websocket_accepts_configured_browser_origin(monkeypatch):
    monkeypatch.setenv("SONICAID_ALLOWED_ORIGINS", "http://localhost:5173")
    client = TestClient(create_app())
    with client.websocket_connect(
        "/ws/stream", headers={"origin": "http://localhost:5173"}
    ) as ws:
        assert ws.receive_json()["status"] == "model_unavailable"


def test_websocket_rejects_oversized_audio_chunks(monkeypatch, tmp_path):
    svc = InferenceService(SessionService(tmp_path), predictor=FixedPredictor())
    monkeypatch.setattr("backend.app.api.routes.stream.get_inference_service", lambda: svc)
    client = TestClient(create_app())
    with client.websocket_connect("/ws/stream") as ws:
        assert ws.receive_json()["status"] == "ready"
        ws.send_bytes(b"\x00\x00" * (16000 * 3))
        with pytest.raises(WebSocketDisconnect) as err:
            ws.receive_json()
        assert err.value.code == 1009
