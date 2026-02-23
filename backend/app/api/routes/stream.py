from fastapi import APIRouter, WebSocket, WebSocketDisconnect

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
    await websocket.accept()
    inference_service = get_inference_service()
    session_id = inference_service.start_session()

    sequence_index = 0

    try:
        while True:
            payload = await websocket.receive_bytes()
            metadata = AudioChunkMetadata(
                session_id=session_id,
                sequence_index=sequence_index,
                sample_rate=16000,
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
        inference_service.end_session(session_id)

