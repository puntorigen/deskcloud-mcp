"""
Session Schemas
===============

Pydantic models for session-related API requests and responses.
Provides validation, serialization, and documentation for the API.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .message import MessageResponse


class SessionStatus(str, Enum):
    """
    Session status values for API responses.
    
    Mirrors the database enum but as a string enum for JSON serialization.
    """
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    ARCHIVED = "archived"


class SessionCreate(BaseModel):
    """
    Request body for creating a new session.
    
    All fields are optional with sensible defaults.
    
    Example:
        POST /api/v1/sessions
        {
            "title": "Weather Search Task",
            "model": "claude-sonnet-4-5-20250929"
        }
    """
    
    title: str | None = Field(
        default=None,
        max_length=255,
        description="Human-readable session title. Auto-generated if not provided.",
        examples=["Weather search task", "Code review session"],
    )
    
    model: str | None = Field(
        default=None,
        max_length=100,
        description="Claude model identifier. Uses default if not specified.",
        examples=["claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001"],
    )
    
    provider: str = Field(
        default="anthropic",
        pattern="^(anthropic|bedrock|vertex)$",
        description="API provider for the model.",
        examples=["anthropic", "bedrock", "vertex"],
    )
    
    system_prompt_suffix: str | None = Field(
        default=None,
        max_length=10000,
        description="Custom instructions appended to the system prompt.",
        examples=["Always explain your reasoning step by step."],
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Search weather in Santiago, Chile",
                "model": "claude-sonnet-4-5-20250929",
                "provider": "anthropic",
            }
        }
    )


class SessionResponse(BaseModel):
    """
    Response body for session creation and retrieval.
    
    Contains session metadata and VNC connection URL.
    """
    
    id: str = Field(
        description="Unique session identifier",
        examples=["sess_abc123def456"],
    )
    
    title: str | None = Field(
        description="Session title",
        examples=["Weather search task"],
    )
    
    status: SessionStatus = Field(
        description="Current session status",
        examples=[SessionStatus.ACTIVE],
    )
    
    model: str = Field(
        description="Claude model being used",
        examples=["claude-sonnet-4-5-20250929"],
    )
    
    provider: str = Field(
        description="API provider",
        examples=["anthropic"],
    )
    
    created_at: datetime = Field(
        description="Session creation timestamp",
    )
    
    updated_at: datetime = Field(
        description="Last modification timestamp",
    )
    
    vnc_url: str = Field(
        description="URL to access the VNC viewer for this session",
        examples=["http://localhost:6080/vnc.html"],
    )
    
    model_config = ConfigDict(
        from_attributes=True,  # Allow ORM model conversion
        json_schema_extra={
            "example": {
                "id": "sess_abc123def456",
                "title": "Weather search task",
                "status": "active",
                "model": "claude-sonnet-4-5-20250929",
                "provider": "anthropic",
                "created_at": "2024-12-07T10:30:00Z",
                "updated_at": "2024-12-07T10:30:00Z",
                "vnc_url": "http://localhost:6080/vnc.html",
            }
        }
    )


class SessionListResponse(BaseModel):
    """
    Response body for listing sessions.
    
    Contains array of session summaries with pagination metadata.
    """
    
    sessions: list[SessionResponse] = Field(
        description="List of sessions",
    )
    
    total: int = Field(
        description="Total number of sessions (for pagination)",
        examples=[42],
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sessions": [
                    {
                        "id": "sess_abc123",
                        "title": "Weather Santiago",
                        "status": "completed",
                        "model": "claude-sonnet-4-5-20250929",
                        "provider": "anthropic",
                        "created_at": "2024-12-07T10:30:00Z",
                        "updated_at": "2024-12-07T10:35:00Z",
                        "vnc_url": "http://localhost:6080/vnc.html",
                    }
                ],
                "total": 1,
            }
        }
    )


class SessionWithMessages(SessionResponse):
    """
    Session response including full message history.
    
    Extended response for GET /sessions/{id} endpoint.
    """
    
    messages: list[MessageResponse] = Field(
        default_factory=list,
        description="Complete message history for the session",
    )
    
    system_prompt_suffix: str | None = Field(
        default=None,
        description="Custom system prompt suffix if set",
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "sess_abc123def456",
                "title": "Weather search task",
                "status": "active",
                "model": "claude-sonnet-4-5-20250929",
                "provider": "anthropic",
                "created_at": "2024-12-07T10:30:00Z",
                "updated_at": "2024-12-07T10:35:00Z",
                "vnc_url": "http://localhost:6080/vnc.html",
                "system_prompt_suffix": None,
                "messages": [
                    {
                        "id": "msg_001",
                        "role": "user",
                        "content": "Search the weather in Santiago, Chile",
                        "timestamp": "2024-12-07T10:31:00Z",
                    },
                    {
                        "id": "msg_002",
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": "I'll search for Santiago, Chile weather..."}
                        ],
                        "timestamp": "2024-12-07T10:31:05Z",
                    },
                ],
            }
        }
    )

