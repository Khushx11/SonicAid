from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/calibration/{task}")
async def calibration_curve(task: str):
    # Calibration records must come from held-out measured predictions.
    # Do not serve fabricated bins or example ECE values as live metrics.
    raise HTTPException(
        status_code=501,
        detail=f"Calibration metrics for {task} are not available; run held-out evaluation.",
    )
