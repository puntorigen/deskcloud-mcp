"""
Message Schemas
===============

Pydantic models for message-related API requests and responses.
"""

from datetime import datetime
from typing import Any

import bleach
from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageCreate(BaseModel):
    """
    Request body for sending a message to a session.
    
    The content is sanitized to prevent XSS attacks when stored.
    
    Example:
        POST /api/v1/sessions/{session_id}/messages
        {
            "content": "Search the weather in Santiago, Chile"
        }
    """
    
    content: str = Field(
        min_length=1,
        max_length=10000,
        description="Message content to send to the agent",
        examples=["Search the weather in Santiago, Chile", "Open Firefox and go to google.com"],
    )
    
    @field_validator("content", mode="after")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """
        Sanitize message content to prevent XSS.
        
        Removes potentially dangerous HTML tags while preserving
        the text content. Safe for storage and display.
        """
        # Clean HTML but preserve text content
        return bleach.clean(v, tags=[], strip=True)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Search the weather in Santiago, Chile"
            }
        }
    )


class MessageResponse(BaseModel):
    """
    Response model for a single message.
    
    The content can be either a simple string (for user messages)
    or a list of content blocks (for assistant messages with tools).
    """
    
    id: str = Field(
        description="Unique message identifier",
        examples=["msg_xyz789abc"],
    )
    
    role: str = Field(
        description="Message sender role",
        examples=["user", "assistant", "tool"],
    )
    
    content: str | list[dict[str, Any]] | dict[str, Any] = Field(
        description="Message content - string for user, structured for assistant",
        examples=[
            "Search the weather in Santiago, Chile",
            [{"type": "text", "text": "I'll help you search..."}],
        ],
    )
    
    tool_use_id: str | None = Field(
        default=None,
        description="For tool results, the associated tool_use block ID",
        examples=["toolu_abc123"],
    )
    
    timestamp: datetime = Field(
        alias="created_at",
        description="Message creation timestamp",
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,  # Allow both 'timestamp' and 'created_at'
        json_schema_extra={
            "example": {
                "id": "msg_xyz789abc",
                "role": "user",
                "content": "Search the weather in Santiago, Chile",
                "tool_use_id": None,
                "timestamp": "2024-12-07T10:31:00Z",
            }
        }
    )


class MessageSendResponse(BaseModel):
    """
    Response body after sending a message.
    
    Includes the message ID and stream URL for real-time updates.
    """
    
    message_id: str = Field(
        description="ID of the created user message",
        examples=["msg_xyz789"],
    )
    
    status: str = Field(
        default="processing",
        description="Message processing status",
        examples=["processing"],
    )
    
    stream_url: str = Field(
        description="SSE endpoint URL for real-time updates",
        examples=["/api/v1/sessions/sess_abc123/stream"],
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg_xyz789",
                "status": "processing",
                "stream_url": "/api/v1/sessions/sess_abc123/stream",
            }
        }
    )

