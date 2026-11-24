import numpy as np
import pytest

from backend.app.models.stream import AudioChunkMetadata
from backend.app.services.inference_service import InferenceService
from backend.app.services.session_service import SessionService


class DeterministicPredictor:
    def __init__(self):
        self.inputs = []

    def predict(self, samples):
        self.inputs.append(samples.copy())
        return "rain", 0.65


@pytest.mark.asyncio
async def test_streaming_waits_for_full_five_second_window(tmp_path):
    predictor = DeterministicPredictor()
    svc = InferenceService(SessionService(tmp_path), predictor=predictor)
    session_id = svc.start_session()
    for index in range(5):
        metadata = AudioChunkMetadata(
            session_id=session_id, sequence_index=index,
            sample_rate=16000, num_channels=1,
        )
        events = await svc.process_chunk(session_id, metadata, b"\x00\x00" * 16000)
        if index < 4:
            assert events is None
        else:
            assert len(events) == 1
            assert events[0].primary_class == "rain"
            assert events[0].primary_confidence == pytest.approx(0.65)
            assert events[0].emotion is None
            assert events[0].engagement_score is None
            assert events[0].window_start == pytest.approx(0)
            assert events[0].window_end == pytest.approx(5)
    assert len(predictor.inputs) == 1
    assert predictor.inputs[0].shape == (80000,)
    svc.end_session(session_id)


@pytest.mark.asyncio
async def test_no_model_means_no_prediction(tmp_path):
    svc = InferenceService(SessionService(tmp_path), predictor=None)
    session_id = svc.start_session()
    meta = AudioChunkMetadata(
        session_id=session_id, sequence_index=0, sample_rate=16000, num_channels=1
    )
    assert svc.ready is False
    assert await svc.process_chunk(session_id, meta, b"\x00\x00" * 16000) is None
    svc.end_session(session_id)


@pytest.mark.asyncio
async def test_pcm_validation_rejects_odd_bytes(tmp_path):
    svc = InferenceService(SessionService(tmp_path), predictor=DeterministicPredictor())
    sid = svc.start_session()
    meta = AudioChunkMetadata(
        session_id=sid, sequence_index=0, sample_rate=16000, num_channels=1
    )
    with pytest.raises(ValueError, match="PCM"):
        await svc.process_chunk(sid, meta, b"\x00")
    svc.end_session(sid)
