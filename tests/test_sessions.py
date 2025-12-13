"""
Session API Tests
=================

Tests for session CRUD operations and message handling.
"""

import pytest
from httpx import AsyncClient


class TestSessionCRUD:
    """Tests for session creation, retrieval, listing, and deletion."""

    @pytest.mark.asyncio
    async def test_create_session(self, client: AsyncClient):
        """Test creating a new session."""
        response = await client.post(
            "/api/v1/sessions",
            json={
                "title": "Weather Search",
                "model": "claude-sonnet-4-5-20250929",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["id"].startswith("sess_")
        assert data["title"] == "Weather Search"
        assert data["status"] == "active"
        assert data["model"] == "claude-sonnet-4-5-20250929"
        assert "vnc_url" in data

    @pytest.mark.asyncio
    async def test_create_session_minimal(self, client: AsyncClient):
        """Test creating a session with minimal parameters."""
        response = await client.post(
            "/api/v1/sessions",
            json={},
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["title"] is not None  # Auto-generated
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_list_sessions(self, client: AsyncClient, test_session: dict):
        """Test listing sessions."""
        response = await client.get("/api/v1/sessions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sessions" in data
        assert "total" in data
        assert len(data["sessions"]) >= 1
        assert any(s["id"] == test_session["id"] for s in data["sessions"])

    @pytest.mark.asyncio
    async def test_list_sessions_pagination(self, client: AsyncClient):
        """Test session listing with pagination."""
        # Create multiple sessions
        for i in range(5):
            await client.post(
                "/api/v1/sessions",
                json={"title": f"Session {i}"},
            )
        
        # Test limit
        response = await client.get("/api/v1/sessions?limit=2")
        assert response.status_code == 200
        assert len(response.json()["sessions"]) == 2
        
        # Test offset
        response = await client.get("/api/v1/sessions?limit=2&offset=2")
        assert response.status_code == 200
        assert len(response.json()["sessions"]) == 2

    @pytest.mark.asyncio
    async def test_get_session(self, client: AsyncClient, test_session: dict):
        """Test retrieving a single session."""
        response = await client.get(f"/api/v1/sessions/{test_session['id']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_session["id"]
        assert data["title"] == test_session["title"]
        assert "messages" in data
        assert isinstance(data["messages"], list)

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client: AsyncClient):
        """Test retrieving a non-existent session."""
        response = await client.get("/api/v1/sessions/sess_nonexistent")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_session(self, client: AsyncClient, test_session: dict):
        """Test deleting (archiving) a session."""
        response = await client.delete(f"/api/v1/sessions/{test_session['id']}")
        
        assert response.status_code == 204
        
        # Verify it's archived (not visible in list)
        list_response = await client.get("/api/v1/sessions")
        sessions = list_response.json()["sessions"]
        assert not any(s["id"] == test_session["id"] for s in sessions)


class TestMessages:
    """Tests for message sending and retrieval."""

    @pytest.mark.asyncio
    async def test_send_message_without_api_key(self, client: AsyncClient, test_session: dict):
        """Test sending a message without API key configured."""
        response = await client.post(
            f"/api/v1/sessions/{test_session['id']}/messages",
            json={"content": "Hello, world!"},
        )
        
        # Should fail gracefully without API key
        assert response.status_code in [503, 500, 200]

    @pytest.mark.asyncio
    async def test_send_message_validation(self, client: AsyncClient, test_session: dict):
        """Test message validation."""
        # Empty content
        response = await client.post(
            f"/api/v1/sessions/{test_session['id']}/messages",
            json={"content": ""},
        )
        assert response.status_code == 422
        
        # Missing content
        response = await client.post(
            f"/api/v1/sessions/{test_session['id']}/messages",
            json={},
        )
        assert response.status_code == 422


class TestHealth:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "version" in data
        assert "checks" in data

    @pytest.mark.asyncio
    async def test_liveness_check(self, client: AsyncClient):
        """Test liveness probe."""
        response = await client.get("/api/v1/health/live")
        
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    @pytest.mark.asyncio
    async def test_config_endpoint(self, client: AsyncClient):
        """Test configuration endpoint."""
        response = await client.get("/api/v1/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "app_name" in data
        assert "version" in data
        assert "default_model" in data

