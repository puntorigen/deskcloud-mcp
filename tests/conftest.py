"""
Pytest Configuration and Fixtures
=================================

Provides shared fixtures for testing the Claude Computer Use backend.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.models import Base
from app.db.session import get_db
from app.config import settings


# =============================================================================
# Test Database Configuration
# =============================================================================

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a clean database session for each test.
    
    Creates all tables before test and drops them after.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Provide session
    async with test_session_maker() as session:
        yield session
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP client for testing API endpoints.
    
    Overrides the database dependency to use test database.
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    
    app.dependency_overrides.clear()


# =============================================================================
# Helper Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_session(client: AsyncClient) -> dict:
    """
    Create a test session and return its data.
    
    Useful for tests that need an existing session.
    """
    response = await client.post(
        "/api/v1/sessions",
        json={"title": "Test Session", "model": "claude-sonnet-4-5-20250929"},
    )
    assert response.status_code == 201
    return response.json()

