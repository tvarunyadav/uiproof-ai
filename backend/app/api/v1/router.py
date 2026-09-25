from fastapi import APIRouter
from app.api.v1.endpoints import health, audits, projects, auth

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(audits.router, prefix="/audits", tags=["Audits"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
