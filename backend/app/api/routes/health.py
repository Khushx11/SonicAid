from fastapi import APIRouter, HTTPException

from ...services.inference_service import get_inference_service

router = APIRouter()


@router.get("/health", summary="Health check")
async def health() -> dict:
    return {"status": "ok"}



@router.get("/ready", summary="ESC-10 model readiness")
def readiness() -> dict:
    if not get_inference_service().ready:
        raise HTTPException(status_code=503, detail="ESC-10 checkpoint unavailable")
    return {"status": "ready", "model": "ESC-10"}
