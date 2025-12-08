"""
API Routes
==========

FastAPI route modules for different API resources.
"""

from fastapi import APIRouter

from .health import router as health_router
from .sessions import router as sessions_router

# =============================================================================
# Main API Router
# =============================================================================

api_router = APIRouter()

# Include all route modules
api_router.include_router(
    health_router,
    tags=["Health"],
)

api_router.include_router(
    sessions_router,
    prefix="/sessions",
    tags=["Sessions"],
)

__all__ = ["api_router"]

