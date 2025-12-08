"""
Session Manager Service
=======================

High-level orchestration of chat sessions and agent execution.
Manages the lifecycle of sessions and coordinates between:
- Database persistence (via repositories)
- Agent execution (via AgentRunner)
- Real-time streaming (via event queues)

This is the main service layer entry point for session operations.

Design Notes:
- Singleton pattern for global session state management
- In-memory tracking of active sessions and their runners
- Thread-safe operations using asyncio primitives
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from app.config import settings
from app.core.events import Event, EventType
from app.db.models import Session as DBSession
from app.db.models import SessionStatus
from app.db.repositories import SessionRepository
from app.db.session import get_db_context

from .agent_runner import AgentRunner
from .display_manager import display_manager


@dataclass
class ActiveSession:
    """
    Tracks an active session with its runner and state.
    
    Attributes:
        session_id: Database session ID
        runner: AgentRunner instance if executing
        event_queue: Queue for SSE events
        last_activity: Timestamp of last interaction
    """
    session_id: str
    runner: AgentRunner | None = None
    event_queue: asyncio.Queue[Event] = field(default_factory=asyncio.Queue)
    is_processing: bool = False


class SessionManager:
    """
    Manages chat sessions and agent execution.
    
    Provides a clean interface for:
    - Creating and retrieving sessions
    - Sending messages and running agent
    - Streaming events via SSE
    - Session cleanup and archival
    
    Thread Safety:
    - Uses locks for dictionary access
    - Event queues are asyncio-safe
    
    Usage:
        # Usually accessed via the global instance
        from app.services import session_manager
        
        # Create session
        session = await session_manager.create_session(db, title="My Task")
        
        # Send message and get event queue
        queue = await session_manager.send_message(db, session.id, "Hello")
        
        # Stream events
        async for event in session_manager.iter_events(session.id):
            yield event.to_sse()
    """
    
    def __init__(self):
        """Initialize the session manager."""
        # Active sessions keyed by session_id
        self._active_sessions: dict[str, ActiveSession] = {}
        
        # Lock for thread-safe access to _active_sessions
        self._lock = asyncio.Lock()
    
    # =========================================================================
    # Session Lifecycle
    # =========================================================================
    
    async def create_session(
        self,
        repo: SessionRepository,
        title: str | None = None,
        model: str | None = None,
        provider: str = "anthropic",
        system_prompt_suffix: str | None = None,
    ) -> DBSession:
        """
        Create a new chat session with an isolated display.
        
        Args:
            repo: Session repository for database access
            title: Human-readable session title
            model: Claude model identifier
            provider: API provider
            system_prompt_suffix: Custom system prompt addition
        
        Returns:
            Created DBSession instance with display info
        """
        # Use defaults from settings if not provided
        model = model or settings.default_model
        
        # Create in database (without display info initially)
        session = await repo.create_session(
            model=model,
            provider=provider,
            title=title,
            system_prompt_suffix=system_prompt_suffix,
        )
        
        # Create isolated display for this session
        try:
            display_info = await display_manager.create_display(session.id)
            
            # Update session with display information
            await repo.update_session_display(
                session_id=session.id,
                display_num=display_info.display_num,
                vnc_port=display_info.vnc_port,
                novnc_port=display_info.novnc_port,
            )
            
            # Refresh session to get updated display info
            session = await repo.get_session(session.id, include_messages=False)
            
        except Exception as e:
            # Log the error but don't fail session creation
            # The session can still work without a display for testing
            print(f"Warning: Could not create display for session {session.id}: {e}")
        
        # Track as active
        async with self._lock:
            self._active_sessions[session.id] = ActiveSession(
                session_id=session.id,
            )
        
        return session
    
    async def get_session(
        self,
        repo: SessionRepository,
        session_id: str,
    ) -> DBSession | None:
        """
        Get a session by ID.
        
        Args:
            repo: Session repository
            session_id: Session identifier
        
        Returns:
            DBSession or None if not found
        """
        return await repo.get_session(session_id, include_messages=True)
    
    async def delete_session(
        self,
        repo: SessionRepository,
        session_id: str,
    ) -> bool:
        """
        Archive (soft-delete) a session and cleanup its display.
        
        Cancels any running agent, destroys the display, and removes
        from active tracking.
        
        Args:
            repo: Session repository
            session_id: Session to archive
        
        Returns:
            True if session was archived
        """
        # Cancel any running agent
        async with self._lock:
            if session_id in self._active_sessions:
                active = self._active_sessions[session_id]
                if active.runner:
                    await active.runner.cancel()
                del self._active_sessions[session_id]
        
        # Destroy the display for this session
        await display_manager.destroy_display(session_id)
        
        # Archive in database
        return await repo.delete_session(session_id)
    
    # =========================================================================
    # Message Handling
    # =========================================================================
    
    async def send_message(
        self,
        repo: SessionRepository,
        session: DBSession,
        content: str,
    ) -> tuple[str, asyncio.Queue[Event]]:
        """
        Send a user message and start agent execution.
        
        This is the main entry point for user interaction:
        1. Validates session is ready
        2. Persists user message
        3. Creates AgentRunner with session context
        4. Starts agent loop in background
        5. Returns event queue for SSE streaming
        
        Args:
            repo: Session repository
            session: Target session (must be active/completed)
            content: User message content
        
        Returns:
            Tuple of (message_id, event_queue)
        
        Raises:
            ValueError: If session is not in valid state
        """
        # Validate session state
        if session.status == SessionStatus.PROCESSING:
            raise ValueError("Session is already processing a message")
        if session.status == SessionStatus.ARCHIVED:
            raise ValueError("Cannot send to archived session")
        
        # Store user message in database
        user_message = await repo.add_message(
            session_id=session.id,
            role="user",
            content=content,  # Simple string for user messages
        )
        
        # Update last_activity for TTL tracking
        await repo.update_last_activity(session.id)
        
        # Update session status
        await repo.update_session_status(session.id, SessionStatus.PROCESSING)
        
        # Get conversation history for context
        messages = await repo.get_messages_as_anthropic_format(session.id)
        
        # Determine tool version based on model
        tool_version = self._get_tool_version(session.model)
        
        # Get display environment for this session
        display_env = display_manager.get_display_env(session.id)
        
        # Create and configure agent runner
        runner = AgentRunner(
            session_id=session.id,
            model=session.model,
            provider=session.provider,
            system_prompt_suffix=session.system_prompt_suffix or "",
            messages=messages,
            tool_version=tool_version,
            display_env=display_env,
        )
        
        # Track the runner
        async with self._lock:
            if session.id not in self._active_sessions:
                self._active_sessions[session.id] = ActiveSession(session_id=session.id)
            
            active = self._active_sessions[session.id]
            active.runner = runner
            active.is_processing = True
            active.event_queue = runner.event_queue
        
        # Start agent execution (returns immediately, runs in background)
        await runner.run(content, message_id=user_message.id)
        
        # Schedule callback to persist results when done
        asyncio.create_task(
            self._handle_completion(repo, session.id, runner)
        )
        
        return user_message.id, runner.event_queue
    
    async def _handle_completion(
        self,
        repo: SessionRepository,
        session_id: str,
        runner: AgentRunner,
    ) -> None:
        """
        Handle agent completion - persist messages and update status.
        
        Runs as background task, waiting for agent to finish then
        saving all generated messages to the database.
        """
        try:
            # Wait for runner to complete
            if runner._task:
                await runner._task
            
            # Get the final messages from runner
            final_messages = runner.messages
            
            # Find new messages (after the user message we started with)
            # The runner.messages includes all history, we need to persist new ones
            async with get_db_context() as db:
                # Re-create repo with new session
                repo = SessionRepository(db)
                
                # Get current message count
                existing = await repo.get_session_messages(session_id)
                existing_count = len(existing)
                
                # Persist any new messages from runner
                for msg in final_messages[existing_count:]:
                    role = msg.get("role", "assistant")
                    content = msg.get("content", [])
                    
                    # Handle tool results specially
                    tool_use_id = None
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_result":
                                tool_use_id = block.get("tool_use_id")
                                break
                    
                    await repo.add_message(
                        session_id=session_id,
                        role=role,
                        content=content,
                        tool_use_id=tool_use_id,
                    )
                
                # Update session status
                await repo.update_session_status(session_id, SessionStatus.ACTIVE)
                
        except Exception as e:
            print(f"Error handling completion for session {session_id}: {e}")
            
            # Try to update status to error
            try:
                async with get_db_context() as db:
                    repo = SessionRepository(db)
                    await repo.update_session_status(session_id, SessionStatus.ERROR)
            except Exception:
                pass
        
        finally:
            # Clean up active session state
            async with self._lock:
                if session_id in self._active_sessions:
                    self._active_sessions[session_id].is_processing = False
                    self._active_sessions[session_id].runner = None
    
    # =========================================================================
    # Event Streaming
    # =========================================================================
    
    def get_event_queue(self, session_id: str) -> asyncio.Queue[Event] | None:
        """
        Get the event queue for a session.
        
        Returns None if session is not active or not processing.
        """
        active = self._active_sessions.get(session_id)
        if active and active.runner:
            return active.event_queue
        return None
    
    async def iter_events(
        self,
        session_id: str,
        timeout: float = 30.0,
    ):
        """
        Async generator for streaming events from a session.
        
        Yields events from the session's queue with keepalive
        on timeout. Stops when message_complete is received.
        
        Args:
            session_id: Session to stream events from
            timeout: Seconds before keepalive
        
        Yields:
            Event objects
        """
        active = self._active_sessions.get(session_id)
        if not active or not active.runner:
            return
        
        async for event in active.runner.iter_events(timeout):
            yield event
    
    # =========================================================================
    # Utilities
    # =========================================================================
    
    def _get_tool_version(self, model: str) -> str:
        """
        Determine tool version based on model.
        
        Different Claude versions require different tool specifications.
        """
        # Tool version mapping (from streamlit.py)
        if "opus-4-5" in model:
            return "computer_use_20251124"  # Zoomable tool
        elif "sonnet-4-5" in model or "haiku-4-5" in model:
            return "computer_use_20250124"  # Claude 4.5
        elif "sonnet-4" in model or "opus-4" in model:
            return "computer_use_20250429"  # Claude 4
        else:
            return "computer_use_20250124"  # Default
    
    def is_session_processing(self, session_id: str) -> bool:
        """Check if a session is currently processing a message."""
        active = self._active_sessions.get(session_id)
        return active is not None and active.is_processing
    
    async def cancel_processing(self, session_id: str) -> bool:
        """
        Cancel processing for a session.
        
        Returns True if there was something to cancel.
        """
        async with self._lock:
            active = self._active_sessions.get(session_id)
            if active and active.runner:
                await active.runner.cancel()
                active.is_processing = False
                return True
        return False


# =============================================================================
# Global Instance
# =============================================================================

# Singleton session manager for use across the application
session_manager = SessionManager()

