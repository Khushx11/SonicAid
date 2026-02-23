from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SessionMetadata(BaseModel):
    session_id: str
    therapist_id: Optional[str] = None
    client_id_hash: str
    start_time: datetime
    end_time: Optional[datetime] = None
    notes: Optional[str] = None

