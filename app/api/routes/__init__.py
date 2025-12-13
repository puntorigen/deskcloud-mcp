"""
API Routes
==========

FastAPI route modules for different API resources.
"""

from fastapi import APIRouter

from .health import router as health_router
from .llms import router as llms_router
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

# =============================================================================
# Root-Level Routes (outside /api/v1)
# =============================================================================

# LLMs.txt is served at root level, not under /api/v1
# It's included here but will be mounted separately in main.py
llms_router_export = llms_router

__all__ = ["api_router", "llms_router_export"]

