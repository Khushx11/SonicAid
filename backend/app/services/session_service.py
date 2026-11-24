from __future__ import annotations

import csv
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from ..models.stream import PredictionMessage


@dataclass
class SessionEvent:
    t_wall: float
    prediction: PredictionMessage


def _validate_session_id(session_id: str) -> None:
    """Reject path separators or control characters in export identifiers."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session_id):
        raise ValueError("invalid session identifier")


class SessionService:
    """
    In-memory session store with optional disk persistence for reports.
    """

    def __init__(self, storage_dir: Path = Path("storage/sessions")) -> None:
        self._sessions: Dict[str, List[SessionEvent]] = {}
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def start(self, session_id: str) -> None:
        _validate_session_id(session_id)
        self._sessions.setdefault(session_id, [])

    def append_prediction(self, p: PredictionMessage) -> None:
        _validate_session_id(p.session_id)
        self._sessions.setdefault(p.session_id, []).append(
            SessionEvent(t_wall=time.time(), prediction=p)
        )

    def list_sessions(self) -> List[str]:
        return sorted(self._sessions.keys())

    def get_session(self, session_id: str) -> List[SessionEvent]:
        return self._sessions.get(session_id, [])

    def export_csv(self, session_id: str) -> Path:
        _validate_session_id(session_id)
        events = self.get_session(session_id)
        out = self._storage_dir / f"{session_id}.csv"

        with out.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "session_id",
                    "t_wall",
                    "window_start",
                    "window_end",
                    "primary_class",
                    "primary_confidence",
                    "emotion",
                    "noise_intensity",
                    "engagement_score",
                    "latency_ms",
                ]
            )
            for e in events:
                p = e.prediction
                w.writerow(
                    [
                        p.session_id,
                        e.t_wall,
                        p.window_start,
                        p.window_end,
                        p.primary_class,
                        p.primary_confidence,
                        p.emotion,
                        p.noise_intensity,
                        p.engagement_score,
                        p.latency_ms,
                    ]
                )

        return out

    def persist_jsonl(self, session_id: str) -> Optional[Path]:
        _validate_session_id(session_id)
        events = self.get_session(session_id)
        if not events:
            return None
        out = self._storage_dir / f"{session_id}.jsonl"
        with out.open("w") as f:
            for e in events:
                f.write(
                    json.dumps(
                        {
                            "t_wall": e.t_wall,
                            **e.prediction.model_dump(),
                        }
                    )
                    + "\n"
                )
        logger.info("Persisted session {} ({} events) to {}", session_id, len(events), out)
        return out


_session_service_singleton: Optional[SessionService] = None


def get_session_service() -> SessionService:
    global _session_service_singleton
    if _session_service_singleton is None:
        _session_service_singleton = SessionService()
    return _session_service_singleton

