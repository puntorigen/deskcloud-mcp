"""
Service Layer
=============

Business logic for session management, display management,
agent orchestration, and session cleanup.

Multi-Session Architecture:
- DisplayManager: Creates isolated X11 displays per session
- SessionManager: Manages session lifecycle and integrates displays
- AgentRunner: Executes agent on session's specific display
- SessionCleanupService: Auto-destroys idle sessions (TTL enforcement)
"""

from .agent_runner import AgentRunner
from .display_manager import DisplayManager, display_manager
from .session_cleanup import SessionCleanupService, cleanup_service
from .session_manager import SessionManager, session_manager

__all__ = [
    "AgentRunner",
    "DisplayManager",
    "display_manager",
    "SessionCleanupService",
    "cleanup_service",
    "SessionManager",
    "session_manager",
]

