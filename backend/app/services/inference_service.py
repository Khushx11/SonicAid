from __future__ import annotations

import time
from typing import Dict, List, Optional

from loguru import logger

from ..core.config import settings
from ..models.stream import AudioChunkMetadata, PredictionMessage
from .session_service import get_session_service, SessionService


class InferenceService:
    """
    Orchestrates streaming audio inference across sessions.

    For now this is a skeleton that returns mocked predictions while the
    deep learning model and feature pipeline are being implemented.
    """

    def __init__(self, session_service: SessionService) -> None:
        self._sessions: Dict[str, Dict] = {}
        self._session_service = session_service
        logger.info("InferenceService initialized")

    def start_session(self) -> str:
        session_id = f"session-{int(time.time() * 1000)}"
        self._sessions[session_id] = {
            "created_at": time.time(),
            "buffer": bytearray(),
            "last_index": -1,
        }
        self._session_service.start(session_id)
        logger.debug("Started session {}", session_id)
        return session_id

    def end_session(self, session_id: str) -> None:
        self._session_service.persist_jsonl(session_id)
        self._sessions.pop(session_id, None)
        logger.debug("Ended session {}", session_id)

    async def process_chunk(
        self, session_id: str, metadata: AudioChunkMetadata, payload: bytes
    ) -> Optional[List[PredictionMessage]]:
        """
        Process an incoming audio chunk for a session.

        In the skeleton implementation we simply echo a single mocked prediction
        per chunk to validate the streaming path and latency accounting.
        """
        if session_id not in self._sessions:
            logger.warning("Received chunk for unknown session {}", session_id)
            return None

        start_time = time.time()

        session = self._sessions[session_id]
        session["buffer"].extend(payload)
        session["last_index"] = metadata.sequence_index

        # TODO: replace with real windowing + model inference
        window_start = max(0.0, metadata.sequence_index - 1) * settings.streaming.hop_seconds
        window_end = window_start + settings.streaming.window_seconds

        latency_ms = (time.time() - start_time) * 1000.0

        prediction = PredictionMessage(
            session_id=session_id,
            window_start=window_start,
            window_end=window_end,
            primary_class="mock_speech",
            primary_confidence=0.7,
            emotion="calm",
            env_tags=["mock"],
            noise_intensity=0.2,
            engagement_score=0.5,
            latency_ms=latency_ms,
            attention_heatmap=None,
        )

        self._session_service.append_prediction(prediction)
        return [prediction]


def get_inference_service() -> InferenceService:
    # In a real system, this could be wired as a singleton with model weights loaded.
    return InferenceService(session_service=get_session_service())

