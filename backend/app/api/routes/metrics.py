from __future__ import annotations

from fastapi import APIRouter

from ...models.metrics import CalibrationBin, CalibrationCurve


router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/calibration/{task}", response_model=CalibrationCurve)
async def calibration_curve(task: str) -> CalibrationCurve:
    # Stub: real calibration curves should be computed offline during eval.
    bins = [
        CalibrationBin(confidence=0.1, accuracy=0.15, count=100),
        CalibrationBin(confidence=0.3, accuracy=0.28, count=120),
        CalibrationBin(confidence=0.5, accuracy=0.52, count=140),
        CalibrationBin(confidence=0.7, accuracy=0.68, count=110),
        CalibrationBin(confidence=0.9, accuracy=0.85, count=80),
    ]
    return CalibrationCurve(task=task, bins=bins, ece=0.07)

