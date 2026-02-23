import pytest

from backend.app.models.stream import AudioChunkMetadata
from backend.app.services.inference_service import get_inference_service


@pytest.mark.asyncio
async def test_inference_service_process_chunk_returns_prediction():
    svc = get_inference_service()
    session_id = svc.start_session()
    try:
        meta = AudioChunkMetadata(
            session_id=session_id, sequence_index=0, sample_rate=16000, num_channels=1
        )
        preds = await svc.process_chunk(session_id=session_id, metadata=meta, payload=b"\x00\x00" * 1024)
        assert preds is not None
        assert len(preds) == 1
        assert preds[0].session_id == session_id
    finally:
        svc.end_session(session_id)

