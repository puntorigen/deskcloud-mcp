"""
Session Routes
==============

REST and SSE endpoints for session management and agent interaction.

Endpoints:
- POST   /sessions                    Create new session
- GET    /sessions                    List all sessions
- GET    /sessions/{session_id}       Get session with history
- DELETE /sessions/{session_id}       Archive session
- POST   /sessions/{session_id}/messages   Send message to agent
- GET    /sessions/{session_id}/stream     SSE stream for real-time updates
"""

import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.deps import SessionRepoDep, ValidSessionDep, get_vnc_url
from app.api.schemas import (
    MessageCreate,
    SessionCreate,
    SessionListResponse,
    SessionResponse,
    SessionWithMessages,
)
from app.api.schemas.message import MessageResponse, MessageSendResponse
from app.config import settings
from app.core.events import EventType, error_event, keepalive_event
from app.db.models import SessionStatus as DBSessionStatus
from app.services import session_manager

router = APIRouter()


# =============================================================================
# Session CRUD Endpoints
# =============================================================================

@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Session",
    description="Create a new chat session for computer use agent interaction.",
)
async def create_session(
    body: SessionCreate,
    repo: SessionRepoDep,
) -> SessionResponse:
    """
    Create a new chat session with isolated desktop.
    
    Creates an isolated session with its own:
    - Conversation history
    - Configuration
    - X11 display (virtual desktop)
    - VNC connection
    
    The session can then receive messages and stream agent responses via SSE.
    Each session has its own VNC URL for independent desktop viewing.
    
    Returns the created session with session-specific VNC URL.
    """
    session = await session_manager.create_session(
        repo=repo,
        title=body.title,
        model=body.model,
        provider=body.provider,
        system_prompt_suffix=body.system_prompt_suffix,
        anthropic_api_key=body.anthropic_api_key,  # BYOK support
    )
    
    return SessionResponse(
        id=session.id,
        title=session.title,
        status=SessionStatus(session.status.value),
        model=session.model,
        provider=session.provider,
        created_at=session.created_at,
        updated_at=session.updated_at,
        vnc_url=get_vnc_url(session),  # Session-specific VNC URL
    )


@router.get(
    "",
    response_model=SessionListResponse,
    summary="List Sessions",
    description="List all active sessions with pagination.",
)
async def list_sessions(
    repo: SessionRepoDep,
    include_archived: Annotated[
        bool,
        Query(description="Include archived sessions in results"),
    ] = False,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum number of results"),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of results to skip"),
    ] = 0,
) -> SessionListResponse:
    """
    List all sessions with optional filtering.
    
    Returns sessions ordered by creation date (newest first).
    Each session includes its own VNC URL for isolated desktop access.
    Supports pagination via limit/offset parameters.
    """
    sessions = await repo.list_sessions(
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )
    
    # Convert to response models with session-specific VNC URLs
    session_responses = [
        SessionResponse(
            id=s.id,
            title=s.title,
            status=SessionStatus(s.status.value),
            model=s.model,
            provider=s.provider,
            created_at=s.created_at,
            updated_at=s.updated_at,
            vnc_url=get_vnc_url(s),  # Session-specific VNC URL
        )
        for s in sessions
    ]
    
    return SessionListResponse(
        sessions=session_responses,
        total=len(session_responses),  # TODO: Add proper count query
    )


@router.get(
    "/{session_id}",
    response_model=SessionWithMessages,
    summary="Get Session",
    description="Get session details including full message history.",
)
async def get_session(
    session: ValidSessionDep,
) -> SessionWithMessages:
    """
    Get a session with its complete message history.
    
    Returns all messages in chronological order, including
    user messages, assistant responses, and tool results.
    Includes session-specific VNC URL for isolated desktop viewing.
    """
    # Convert messages to response format
    messages = [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            tool_use_id=m.tool_use_id,
            timestamp=m.created_at,
        )
        for m in session.messages
    ]
    
    return SessionWithMessages(
        id=session.id,
        title=session.title,
        status=SessionStatus(session.status.value),
        model=session.model,
        provider=session.provider,
        created_at=session.created_at,
        updated_at=session.updated_at,
        vnc_url=get_vnc_url(session),  # Session-specific VNC URL
        system_prompt_suffix=session.system_prompt_suffix,
        messages=messages,
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Session",
    description="Archive a session (soft delete).",
)
async def delete_session(
    session: ValidSessionDep,
    repo: SessionRepoDep,
) -> None:
    """
    Archive a session.
    
    Soft-deletes the session by changing its status to ARCHIVED.
    Archived sessions are hidden from list but can be retrieved
    directly if needed for auditing.
    
    Also cancels any running agent processes for this session.
    """
    await session_manager.delete_session(repo, session.id)


# =============================================================================
# Message Endpoints
# =============================================================================

@router.post(
    "/{session_id}/messages",
    response_model=MessageSendResponse,
    summary="Send Message",
    description="Send a message to the agent and start processing.",
)
async def send_message(
    session: ValidSessionDep,
    body: MessageCreate,
    repo: SessionRepoDep,
) -> MessageSendResponse:
    """
    Send a user message to the session's agent.
    
    This triggers the agent to:
    1. Process the message
    2. Execute any required tools (screenshots, clicks, etc.)
    3. Stream responses via SSE
    
    The response includes a stream_url to connect for real-time updates.
    
    Note: Only one message can be processed at a time per session.
    """
    # Check if session is already processing
    if session_manager.is_session_processing(session.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session is already processing a message. Wait for completion or cancel.",
        )
    
    # Check if API key is available (either server-side or BYOK from session)
    # BYOK key is checked in session_manager, here we just verify there's a fallback
    has_server_key = bool(settings.anthropic_api_key.get_secret_value())
    has_session_key = session_manager.has_api_key(session.id)
    
    if not has_server_key and not has_session_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No API key configured. Either set ANTHROPIC_API_KEY or provide your own key when creating the session.",
        )
    
    try:
        # Send message and get event queue
        message_id, _ = await session_manager.send_message(
            repo=repo,
            session=session,
            content=body.content,
        )
        
        return MessageSendResponse(
            message_id=message_id,
            status="processing",
            stream_url=f"{settings.api_v1_prefix}/sessions/{session.id}/stream",
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}",
        )


# =============================================================================
# SSE Streaming Endpoint
# =============================================================================

@router.get(
    "/{session_id}/stream",
    summary="Stream Events",
    description="Server-Sent Events endpoint for real-time agent updates.",
    responses={
        200: {
            "description": "SSE stream of agent events",
            "content": {
                "text/event-stream": {
                    "example": "event: text\ndata: {\"content\": \"I'll help...\"}\n\n"
                }
            },
        },
    },
)
async def stream_session(
    session: ValidSessionDep,
) -> StreamingResponse:
    """
    Stream real-time events from agent execution.
    
    Provides Server-Sent Events (SSE) stream with:
    - text: Agent text responses
    - thinking: Extended thinking content
    - tool_use: Tool invocation notifications
    - tool_result: Tool execution results (may include screenshots)
    - message_complete: Processing finished
    - error: Error notifications
    - keepalive: Connection maintenance (every 30s)
    
    Connect immediately after sending a message. The stream will
    emit events until message_complete or error is received.
    
    Example client code (JavaScript):
    ```javascript
    const eventSource = new EventSource('/api/v1/sessions/{id}/stream');
    eventSource.addEventListener('text', (e) => {
        const data = JSON.parse(e.data);
        console.log('Agent said:', data.content);
    });
    eventSource.addEventListener('message_complete', () => {
        eventSource.close();
    });
    ```
    """
    async def event_generator():
        """
        Async generator that yields SSE-formatted events.
        
        Handles:
        - Active processing: streams from session's event queue
        - No active processing: sends single "no_activity" event
        - Timeouts: sends keepalive events
        - Completion: breaks on message_complete
        """
        # Check if session is processing
        if not session_manager.is_session_processing(session.id):
            # Not processing - send status and close
            event = error_event(
                error="No active processing for this session",
                code="NO_ACTIVITY",
            )
            yield event.to_sse()
            return
        
        # Stream events from session
        try:
            async for event in session_manager.iter_events(session.id, timeout=30.0):
                yield event.to_sse()
                
                # Stop on completion
                if event.type == EventType.MESSAGE_COMPLETE:
                    break
                    
        except asyncio.CancelledError:
            # Client disconnected - clean shutdown
            pass
        except Exception as e:
            # Unexpected error - emit and close
            err = error_event(error=str(e), code="STREAM_ERROR")
            yield err.to_sse()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",  # CORS for SSE
        },
    )


@router.post(
    "/{session_id}/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel Processing",
    description="Cancel ongoing agent processing for a session.",
)
async def cancel_processing(
    session: ValidSessionDep,
    repo: SessionRepoDep,
) -> dict[str, str]:
    """
    Cancel ongoing agent processing.
    
    Stops the current agent execution and returns the session
    to active state. Any partial results are preserved.
    
    Useful for:
    - User-initiated cancellation
    - Timeout handling
    - Error recovery
    """
    cancelled = await session_manager.cancel_processing(session.id)
    
    if cancelled:
        # Update session status
        await repo.update_session_status(session.id, DBSessionStatus.ACTIVE)
        return {"status": "cancelled", "message": "Processing cancelled successfully"}
    else:
        return {"status": "not_processing", "message": "No active processing to cancel"}


# =============================================================================
# Import SessionStatus for response serialization
# =============================================================================

from app.api.schemas.session import SessionStatus

