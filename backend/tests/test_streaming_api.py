import pytest
from fastapi.testclient import TestClient

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

