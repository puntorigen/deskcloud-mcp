"""
Service Layer
=============

Business logic for session management, display management,
and agent orchestration.

Multi-Session Architecture:
- DisplayManager: Creates isolated X11 displays per session
- SessionManager: Manages session lifecycle and integrates displays
- AgentRunner: Executes agent on session's specific display
"""

from .agent_runner import AgentRunner
from .display_manager import DisplayManager, display_manager
from .session_manager import SessionManager, session_manager

__all__ = [
    "AgentRunner",
    "DisplayManager",
    "display_manager",
    "SessionManager",
    "session_manager",
]

