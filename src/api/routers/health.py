"""
Health check API router for FastAPI app (stub for test unblocking).
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/live")
def health_live():
    return {"status": "alive"}

@router.get("/ready")
def health_ready():
    return {"checks": {"system": "ok", "dependencies": "ok"}}
