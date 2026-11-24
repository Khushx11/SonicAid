from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...core.config import allowed_cors_origins, settings
from ...models.stream import AudioChunkMetadata
from ...services.inference_service import get_inference_service


router = APIRouter()


@router.websocket("/ws/stream")
async def stream_audio(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for streaming audio chunks and returning predictions.

    The client sends raw PCM chunks as binary messages along with minimal
    metadata encoded in the subprotocol or query parameters (for this
    skeleton we derive metadata server-side and assume 16 kHz mono).
    """
    # Browser WebSockets are not covered by HTTP CORS middleware. Reject
    # unexpected Origin headers; non-browser clients may omit Origin.
    origin = websocket.headers.get("origin")
    if origin is not None and origin not in allowed_cors_origins():
        await websocket.close(code=1008)
        return

    await websocket.accept()
    inference_service = get_inference_service()
    session_id = inference_service.start_session()

    sequence_index = 0
    max_chunk_bytes = int(
        settings.streaming.sample_rate
        * 2  # 16-bit mono samples are two bytes each
        * settings.streaming.max_chunk_seconds
    )

    try:
        while True:
            payload = await websocket.receive_bytes()
            if len(payload) > max_chunk_bytes:
                await websocket.close(code=1009)
                break
            metadata = AudioChunkMetadata(
                session_id=session_id,
                sequence_index=sequence_index,
                sample_rate=settings.streaming.sample_rate,
                num_channels=1,
            )
            sequence_index += 1

            predictions = await inference_service.process_chunk(
                session_id=session_id,
                metadata=metadata,
                payload=payload,
            )

            if predictions:
                for p in predictions:
                    await websocket.send_json(p.model_dump())
    except WebSocketDisconnect:
        pass
    finally:
        inference_service.end_session(session_id)

