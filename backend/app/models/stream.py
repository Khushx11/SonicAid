from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AudioChunkMetadata(BaseModel):
    session_id: str
    sequence_index: int
    sample_rate: int
    num_channels: int
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Server receive time for this chunk.",
    )


class PredictionMessage(BaseModel):
    session_id: str
    window_start: float
    window_end: float
    primary_class: str
    primary_confidence: float
    emotion: str
    env_tags: List[str]
    noise_intensity: float
    engagement_score: float
    latency_ms: float
    attention_heatmap: Optional[List[List[float]]] = None


