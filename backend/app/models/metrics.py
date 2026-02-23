from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class CalibrationBin(BaseModel):
    confidence: float = Field(ge=0.0, le=1.0)
    accuracy: float = Field(ge=0.0, le=1.0)
    count: int = Field(ge=0)


class CalibrationCurve(BaseModel):
    task: str
    bins: List[CalibrationBin]
    ece: float = Field(ge=0.0)

