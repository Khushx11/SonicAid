import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.app.main import create_app


@pytest.mark.parametrize("n_chunks", [1, 3])
def test_websocket_stream_returns_predictions(n_chunks: int):
    app = create_app()
    client = TestClient(app)

    with client.websocket_connect("/ws/stream") as ws:
        for _ in range(n_chunks):
            ws.send_bytes(b"\x00\x00" * 1024)
            msg = ws.receive_json()
            assert "primary_class" in msg
            assert "primary_confidence" in msg
            assert "latency_ms" in msg



def test_websocket_blocks_unknown_browser_origin(monkeypatch):
    monkeypatch.setenv("SONICAID_ALLOWED_ORIGINS", "http://localhost:5173")
    client = TestClient(create_app())
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            "/ws/stream",
            headers={"origin": "https://malicious.example"},
        ):
            pass


def test_websocket_accepts_configured_browser_origin(monkeypatch):
    monkeypatch.setenv("SONICAID_ALLOWED_ORIGINS", "http://localhost:5173")
    client = TestClient(create_app())
    with client.websocket_connect(
        "/ws/stream",
        headers={"origin": "http://localhost:5173"},
    ) as ws:
        ws.send_bytes(b"\x00\x00" * 1024)
        assert ws.receive_json()["primary_class"] == "mock_speech"
