"""
Event System for Real-time Streaming
=====================================

Defines event types and serialization for Server-Sent Events (SSE).
These events are emitted by the agent runner and consumed by the SSE endpoint.

Event Flow:
1. Agent runner executes sampling_loop with callbacks
2. Callbacks create Event objects and push to async queue
3. SSE endpoint consumes queue and formats as SSE text

SSE Format:
    event: {event_type}
    data: {json_payload}
    
    (blank line to separate events)
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class EventType(StrEnum):
    """
    Types of events emitted during agent execution.
    
    These map directly to SSE event names, allowing the frontend
    to subscribe to specific event types via EventSource.addEventListener().
    """
    
    # Session lifecycle events
    MESSAGE_START = "message_start"
    MESSAGE_COMPLETE = "message_complete"
    
    # Content events from Claude
    TEXT = "text"
    THINKING = "thinking"
    TOOL_USE = "tool_use"
    
    # Tool execution events
    TOOL_RESULT = "tool_result"
    
    # Error and status events
    ERROR = "error"
    STATUS = "status"
    
    # Connection management
    KEEPALIVE = "keepalive"


@dataclass
class Event:
    """
    Represents a single SSE event.
    
    Attributes:
        type: Event type for SSE routing
        data: Payload to be JSON-serialized
        timestamp: When the event was created (ISO format)
        message_id: Associated message ID (if applicable)
    
    Example:
        event = Event(
            type=EventType.TEXT,
            data={"content": "I'll search for the weather..."}
        )
        sse_text = event.to_sse()
        # "event: text\ndata: {\"content\": \"I'll search...\"}\n\n"
    """
    
    type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    message_id: str | None = None
    
    def to_sse(self) -> str:
        """
        Format event as SSE text.
        
        Returns properly formatted Server-Sent Event string with
        event type, JSON data, and required blank line terminator.
        """
        # Include metadata in the payload
        payload = {
            **self.data,
            "timestamp": self.timestamp,
        }
        if self.message_id:
            payload["message_id"] = self.message_id
            
        # Format as SSE: event line, data line, blank line
        return f"event: {self.type}\ndata: {json.dumps(payload)}\n\n"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for storage or logging."""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
        }


def create_event(
    event_type: EventType,
    message_id: str | None = None,
    **data: Any,
) -> Event:
    """
    Factory function to create events with consistent structure.
    
    Args:
        event_type: Type of event to create
        message_id: Optional message ID to associate
        **data: Event payload data
    
    Returns:
        Configured Event instance
    
    Example:
        event = create_event(
            EventType.TEXT,
            message_id="msg_123",
            content="Hello, world!"
        )
    """
    return Event(
        type=event_type,
        data=data,
        message_id=message_id,
    )


# =============================================================================
# Convenience functions for common events
# =============================================================================

def text_event(content: str, message_id: str | None = None) -> Event:
    """Create a text content event."""
    return create_event(EventType.TEXT, message_id, content=content)


def thinking_event(content: str, message_id: str | None = None) -> Event:
    """Create a thinking/reasoning event."""
    return create_event(EventType.THINKING, message_id, content=content)


def tool_use_event(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_use_id: str,
    message_id: str | None = None,
) -> Event:
    """Create a tool invocation event."""
    return create_event(
        EventType.TOOL_USE,
        message_id,
        tool=tool_name,
        input=tool_input,
        tool_use_id=tool_use_id,
    )


def tool_result_event(
    tool_use_id: str,
    output: str | None = None,
    error: str | None = None,
    screenshot: str | None = None,
    message_id: str | None = None,
) -> Event:
    """Create a tool result event."""
    data = {"tool_use_id": tool_use_id}
    if output:
        data["output"] = output
    if error:
        data["error"] = error
    if screenshot:
        data["screenshot"] = screenshot  # Base64-encoded image
    return create_event(EventType.TOOL_RESULT, message_id, **data)


def error_event(
    error: str,
    code: str | None = None,
    retry_after: int | None = None,
    message_id: str | None = None,
) -> Event:
    """Create an error event."""
    data = {"error": error}
    if code:
        data["code"] = code
    if retry_after:
        data["retry_after"] = retry_after
    return create_event(EventType.ERROR, message_id, **data)


def message_complete_event(
    message_id: str,
    status: str = "completed",
) -> Event:
    """Create a message completion event."""
    return create_event(
        EventType.MESSAGE_COMPLETE,
        message_id,
        status=status,
    )


def keepalive_event() -> Event:
    """Create a keepalive event to maintain SSE connection."""
    return create_event(EventType.KEEPALIVE)

