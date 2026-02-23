from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ...services.session_service import get_session_service


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", summary="List active sessions")
async def list_sessions() -> dict:
    svc = get_session_service()
    return {"sessions": svc.list_sessions()}


@router.get("/{session_id}/export.csv", summary="Export session CSV")
async def export_session_csv(session_id: str):
    svc = get_session_service()
    if session_id not in svc.list_sessions():
        raise HTTPException(status_code=404, detail="Session not found")
    path = svc.export_csv(session_id)
    return FileResponse(path)

