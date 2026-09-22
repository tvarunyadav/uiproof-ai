from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone
from app.config import settings

router = APIRouter()


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime


@router.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """System status and readiness check."""
    return HealthCheckResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc)
    )
