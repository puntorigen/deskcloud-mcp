"""
FastAPI Dependencies
====================

Reusable dependencies for route handlers.
Provides database sessions, repositories, and common patterns.
"""

from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Session as DBSession
from app.db import get_db
from app.db.repositories import SessionRepository


# =============================================================================
# Database Dependencies
# =============================================================================

async def get_session_repository(
    db: AsyncSession = Depends(get_db),
) -> SessionRepository:
    """
    Dependency that provides a SessionRepository instance.
    
    Wraps the database session in a repository for cleaner access.
    """
    return SessionRepository(db)


# Type alias for cleaner route signatures
SessionRepoDep = Annotated[SessionRepository, Depends(get_session_repository)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db)]


# =============================================================================
# Path Parameter Dependencies
# =============================================================================

async def get_valid_session(
    session_id: Annotated[str, Path(description="Session ID", examples=["sess_abc123"])],
    repo: SessionRepoDep,
) -> DBSession:
    """
    Dependency that validates session_id and returns the session.
    
    Raises 404 if session not found or archived.
    
    Usage:
        @router.get("/sessions/{session_id}")
        async def get_session(session: DBSession = Depends(get_valid_session)):
            return session
    """
    session = await repo.get_session(session_id, include_messages=True)
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    
    # Don't return archived sessions
    from app.db.models import SessionStatus
    if session.status == SessionStatus.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' has been archived",
        )
    
    return session


# Type alias for valid session dependency
ValidSessionDep = Annotated[DBSession, Depends(get_valid_session)]


# =============================================================================
# Utility Dependencies
# =============================================================================

def get_vnc_url() -> str:
    """
    Get the VNC viewer URL from configuration.
    
    In production with reverse proxy, this would be a relative URL.
    """
    from app.config import settings
    return settings.vnc_base_url

