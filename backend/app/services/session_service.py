from __future__ import annotations

import csv
import io
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


class SessionLimitError(RuntimeError):
    pass


class SessionService:
    """
    In-memory session store with optional disk persistence for reports.
    """

    MAX_ACTIVE = 16
    MAX_COMPLETED = 16
    MAX_EVENTS = 7_200

    def __init__(self, storage_dir: Path = Path("storage/sessions")) -> None:
        self._sessions: Dict[str, List[SessionEvent]] = {}
        self._active: set[str] = set()
        self._completed: list[str] = []
        self._storage_dir = storage_dir

    def start(self, session_id: str) -> None:
        _validate_session_id(session_id)
        if session_id in self._sessions:
            return
        if len(self._active) >= self.MAX_ACTIVE:
            raise SessionLimitError("Too many active audio sessions")
        self._active.add(session_id)
        self._sessions[session_id] = []

    def finish(self, session_id: str) -> None:
        if session_id not in self._active:
            return
        self._active.remove(session_id)
        if not self._sessions[session_id]:
            del self._sessions[session_id]
            return
        self._completed.append(session_id)
        while len(self._completed) > self.MAX_COMPLETED:
            del self._sessions[self._completed.pop(0)]

    def append_prediction(self, p: PredictionMessage) -> None:
        _validate_session_id(p.session_id)
        if p.session_id not in self._active:
            if p.session_id in self._sessions:
                return
            self.start(p.session_id)
        events = self._sessions[p.session_id]
        if len(events) < self.MAX_EVENTS:
            events.append(SessionEvent(t_wall=time.time(), prediction=p))

    def list_sessions(self) -> List[str]:
        return sorted(self._sessions.keys())

    def get_session(self, session_id: str) -> List[SessionEvent]:
        return self._sessions.get(session_id, [])

    def csv_text(self, session_id: str) -> str:
        _validate_session_id(session_id)
        events = self.get_session(session_id)
        stream = io.StringIO(newline="")
        w = csv.writer(stream)
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

        return stream.getvalue()

    def export_csv(self, session_id: str) -> Path:
        content = self.csv_text(session_id)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        out = self._storage_dir / f"{session_id}.csv"
        out.write_text(content, encoding="utf-8", newline="")
        return out

    def persist_jsonl(self, session_id: str) -> Optional[Path]:
        _validate_session_id(session_id)
        events = self.get_session(session_id)
        if not events:
            return None
        self._storage_dir.mkdir(parents=True, exist_ok=True)
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

