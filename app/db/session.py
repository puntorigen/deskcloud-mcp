"""
Database Session Management
===========================

Provides async database session factory and initialization.
Uses SQLAlchemy's async engine for non-blocking database operations.

Usage:
    # In FastAPI dependency
    async def get_db():
        async with async_session_maker() as session:
            yield session
    
    # Initialize database (creates tables)
    await init_db()
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

from .models import Base

# =============================================================================
# Engine Configuration
# =============================================================================

# Ensure data directory exists for SQLite
if settings.database_url.startswith("sqlite"):
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)

# Create async engine with appropriate settings
# Note: check_same_thread=False is required for SQLite with async
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    # SQLite-specific: allow multi-threaded access
    connect_args={"check_same_thread": False} 
    if settings.database_url.startswith("sqlite") 
    else {},
)

# =============================================================================
# Session Factory
# =============================================================================

# Session maker for creating async database sessions
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,
    autoflush=False,
)


# =============================================================================
# FastAPI Dependency
# =============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.
    
    Yields an async session that will be automatically closed
    after the request completes. Handles commit/rollback.
    
    Usage:
        @router.get("/sessions")
        async def list_sessions(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of FastAPI.
    
    Useful for background tasks or CLI commands.
    
    Usage:
        async with get_db_context() as db:
            session = await db.get(Session, session_id)
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# =============================================================================
# Database Initialization
# =============================================================================

async def init_db() -> None:
    """
    Initialize database by creating all tables.
    
    Safe to call multiple times - will not drop existing data.
    Uses SQLAlchemy's create_all which is idempotent.
    """
    async with engine.begin() as conn:
        # Create all tables defined in models
        await conn.run_sync(Base.metadata.create_all)
    
    print(f"✅ Database initialized: {settings.database_url}")


async def drop_db() -> None:
    """
    Drop all tables (DANGEROUS - for testing only).
    
    This will permanently delete all data!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("⚠️  Database dropped!")


# =============================================================================
# Synchronous initialization for entrypoint scripts
# =============================================================================

def init_db_sync() -> None:
    """
    Synchronous wrapper for database initialization.
    
    Used by entrypoint scripts that can't easily run async code.
    
    Usage (in shell script):
        python -c "from app.db.session import init_db_sync; init_db_sync()"
    """
    import asyncio
    asyncio.run(init_db())

