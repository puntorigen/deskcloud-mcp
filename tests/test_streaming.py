"""
Streaming Tests
===============

Tests for SSE streaming functionality.
"""

import pytest
from httpx import AsyncClient


class TestSSEStreaming:
    """Tests for Server-Sent Events streaming."""

    @pytest.mark.asyncio
    async def test_stream_without_processing(self, client: AsyncClient, test_session: dict):
        """Test streaming when no message is being processed."""
        # Connect to stream without sending a message first
        async with client.stream(
            "GET",
            f"/api/v1/sessions/{test_session['id']}/stream",
        ) as response:
            assert response.status_code == 200
            
            # Should receive an error event about no activity
            lines = []
            async for line in response.aiter_lines():
                lines.append(line)
                # Only read first few lines
                if len(lines) > 5:
                    break
            
            # Check that we got some response
            content = "\n".join(lines)
            assert "event:" in content or "data:" in content

    @pytest.mark.asyncio
    async def test_stream_headers(self, client: AsyncClient, test_session: dict):
        """Test that SSE headers are set correctly."""
        async with client.stream(
            "GET",
            f"/api/v1/sessions/{test_session['id']}/stream",
        ) as response:
            assert response.status_code == 200
            assert response.headers.get("content-type") == "text/event-stream; charset=utf-8"
            assert response.headers.get("cache-control") == "no-cache"


class TestCancelProcessing:
    """Tests for cancellation functionality."""

    @pytest.mark.asyncio
    async def test_cancel_not_processing(self, client: AsyncClient, test_session: dict):
        """Test cancelling when nothing is processing."""
        response = await client.post(
            f"/api/v1/sessions/{test_session['id']}/cancel",
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_processing"

