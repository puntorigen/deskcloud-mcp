"""
Health Check Endpoints
======================

Provides health and readiness checks for monitoring and orchestration.
Used by Docker health checks, load balancers, and Kubernetes probes.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema."""
    
    status: str = Field(
        description="Overall health status",
        examples=["healthy", "degraded", "unhealthy"],
    )
    version: str = Field(
        description="Application version",
    )
    timestamp: str = Field(
        description="Current server timestamp (ISO format)",
    )
    checks: dict[str, Any] = Field(
        default_factory=dict,
        description="Individual component health checks",
    )


class ConfigResponse(BaseModel):
    """Configuration info response (non-sensitive)."""
    
    app_name: str
    version: str
    api_provider: str
    default_model: str
    vnc_url: str
    available_providers: list[str] = ["anthropic", "bedrock", "vertex"]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the health status of the application and its dependencies.",
)
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> HealthResponse:
    """
    Comprehensive health check endpoint.
    
    Checks:
    - Database connectivity
    - API key configuration
    - Overall application status
    
    Returns 200 even if degraded (for monitoring differentiation).
    Use /health/ready for strict readiness checks.
    """
    checks: dict[str, Any] = {}
    overall_status = "healthy"
    
    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy", "type": "sqlite"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_status = "degraded"
    
    # Check API key configuration
    api_key = settings.anthropic_api_key.get_secret_value()
    if api_key:
        checks["api_key"] = {"status": "configured", "provider": settings.api_provider}
    else:
        checks["api_key"] = {"status": "not_configured"}
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat() + "Z",
        checks=checks,
    )


@router.get(
    "/health/ready",
    summary="Readiness Check",
    description="Strict readiness check - returns 503 if not fully ready.",
)
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Strict readiness probe for orchestrators.
    
    Returns 200 only if all dependencies are ready.
    Used by Kubernetes/Docker for traffic routing decisions.
    """
    # Check database
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not ready: {e}",
        )
    
    # Check API key
    if not settings.anthropic_api_key.get_secret_value():
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key not configured",
        )
    
    return {"status": "ready"}


@router.get(
    "/health/live",
    summary="Liveness Check",
    description="Simple liveness check - returns 200 if process is running.",
)
async def liveness_check() -> dict[str, str]:
    """
    Simple liveness probe.
    
    Always returns 200 if the process is running.
    Used to detect if the application has crashed or deadlocked.
    """
    return {"status": "alive"}


@router.get(
    "/config",
    response_model=ConfigResponse,
    summary="Get Configuration",
    description="Returns non-sensitive application configuration.",
)
async def get_config() -> ConfigResponse:
    """
    Return public configuration information.
    
    Useful for clients to discover available options
    without exposing sensitive data.
    """
    return ConfigResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        api_provider=settings.api_provider,
        default_model=settings.default_model,
        vnc_url=settings.vnc_base_url,
    )

