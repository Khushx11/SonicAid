import pytest

from backend.app.core.config import settings
from backend.app.models.stream import AudioChunkMetadata
from backend.app.services.inference_service import InferenceService
from backend.app.services.session_service import SessionService


class TestPredictor:
    def predict(self, samples):
        return "rain", 0.6


def test_sessions_use_distinct_identifiers(tmp_path, monkeypatch):
    # Even if the wall-clock is fixed, new sessions must not collide.
    monkeypatch.setattr("backend.app.services.inference_service.time.time", lambda: 1000.0)
    service = InferenceService(SessionService(storage_dir=tmp_path))
    first = service.start_session()
    second = service.start_session()
    assert first != second
    assert first.startswith("session-")
    assert second.startswith("session-")


@pytest.mark.asyncio
async def test_audio_memory_is_bounded_across_chunks(tmp_path):
    service = InferenceService(SessionService(storage_dir=tmp_path), predictor=TestPredictor())
    session_id = service.start_session()
    max_bytes = int(settings.streaming.sample_rate * settings.streaming.window_seconds) * 2

    for index in range(4):
        metadata = AudioChunkMetadata(
            session_id=session_id,
            sequence_index=index,
            sample_rate=settings.streaming.sample_rate,
            num_channels=1,
        )
        predictions = await service.process_chunk(
            session_id=session_id,
            metadata=metadata,
            payload=b"\x01\x00" * (max_bytes + 1024),
        )
        assert predictions is not None
        assert predictions[0].primary_class == "rain"
        assert len(service._sessions[session_id]["buffer"]) <= max_bytes

    service.end_session(session_id)
    assert session_id not in service._sessions
