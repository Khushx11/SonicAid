"""Streaming environmental-sound inference (not clinical measurement)."""
from __future__ import annotations

import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import numpy as np
from loguru import logger

from ..core.config import settings
from ..models.stream import AudioChunkMetadata, PredictionMessage
from .session_service import SessionService, get_session_service


class InferenceService:
    """Bounded PCM16 windows with real ESC-10 inference when weights are installed.

    The server never fabricates predictions in the absence of a checkpoint.
    Model outputs are environmental sound categories only.
    """

    def __init__(self, session_service: SessionService, predictor=None) -> None:
        self._sessions: Dict[str, Dict] = {}
        self._session_service = session_service
        self._predictor = predictor

    @property
    def ready(self) -> bool:
        return self._predictor is not None

    def start_session(self) -> str:
        session_id = f"session-{uuid4().hex}"
        self._session_service.start(session_id)
        self._sessions[session_id] = {
            "created_at": time.time(),
            "buffer": bytearray(),
            "total_samples": 0,
            "last_emitted_samples": 0,
        }
        return session_id

    def end_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        self._session_service.finish(session_id)

    async def process_chunk(
        self, session_id: str, metadata: AudioChunkMetadata, payload: bytes
    ) -> Optional[List[PredictionMessage]]:
        if session_id not in self._sessions:
            return None
        if not self.ready:
            return None
        if metadata.sample_rate != settings.streaming.sample_rate or metadata.num_channels != 1:
            raise ValueError("expected mono PCM16 at configured sample rate")
        if not payload or len(payload) % 2:
            raise ValueError("expected complete 16-bit PCM samples")

        started = time.perf_counter()
        state = self._sessions[session_id]
        sample_count = len(payload) // 2
        window_samples = int(settings.streaming.window_seconds * settings.streaming.sample_rate)
        hop_samples = max(1, int(settings.streaming.hop_seconds * settings.streaming.sample_rate))
        window_bytes = 2 * window_samples

        state["total_samples"] += sample_count
        state["buffer"].extend(payload)
        if len(state["buffer"]) > window_bytes:
            del state["buffer"][:-window_bytes]

        if state["total_samples"] < window_samples:
            return None
        if (state["last_emitted_samples"]
                and state["total_samples"] - state["last_emitted_samples"] < hop_samples):
            return None

        # PCM16 little-endian, normalized to [-1, 1].
        samples = np.frombuffer(bytes(state["buffer"]), dtype="<i2").astype(np.float32) / 32768.0
        label, confidence = self._predictor.predict(samples)
        state["last_emitted_samples"] = state["total_samples"]
        end_seconds = state["total_samples"] / settings.streaming.sample_rate

        result = PredictionMessage(
            session_id=session_id,
            window_start=max(0.0, end_seconds - settings.streaming.window_seconds),
            window_end=end_seconds,
            primary_class=label,
            primary_confidence=confidence,
            emotion=None, env_tags=["esc10_environmental_sound"],
            noise_intensity=None, engagement_score=None,
            latency_ms=(time.perf_counter() - started) * 1000,
            attention_heatmap=None,
        )
        self._session_service.append_prediction(result)
        return [result]


@lru_cache(maxsize=1)
def load_predictor(path: Path, modified_ns: int, size: int):
    # File metadata invalidates the cache when a trusted checkpoint changes.
    from ml.real_audio.esc10 import ESC10Predictor

    return ESC10Predictor(path)


def get_inference_service() -> InferenceService:
    predictor = None
    model = os.environ.get("SONICAID_ESC10_MODEL")
    if model:
        path = Path(model)
        if path.is_file():
            # joblib deserialization is unsafe on untrusted uploads.
            # Only set the environment variable to a locally trained checkpoint.
            metadata = path.stat()
            predictor = load_predictor(path.resolve(), metadata.st_mtime_ns, metadata.st_size)
        else:
            logger.warning("ESC-10 checkpoint not found: {}", path)
    return InferenceService(session_service=get_session_service(), predictor=predictor)
