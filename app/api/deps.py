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

def get_vnc_url(session: DBSession | None = None) -> str:
    """
    Get the VNC viewer URL for a session using token-based routing.
    
    Uses websockify token-based routing: single noVNC on port 6080,
    with session_id as token for routing to the correct VNC backend.
    
    Args:
        session: Optional session to get VNC URL for
    
    Returns:
        noVNC web URL with token for VNC access
    """
    from app.config import settings
    from app.services.display_manager import display_manager
    
    # If session provided, try to get token-based URL from display manager
    if session:
        vnc_url = display_manager.get_vnc_url(session.id)
        if vnc_url:
            return vnc_url
    
    # Fallback to base VNC URL (no token - for API info endpoints)
    return settings.vnc_base_url


def get_session_vnc_url(session_id: str) -> str | None:
    """
    Get VNC URL for a session from the display manager.
    
    Args:
        session_id: Session identifier
    
    Returns:
        noVNC URL with token or None if no display exists
    """
    from app.services.display_manager import display_manager
    return display_manager.get_vnc_url(session_id)

