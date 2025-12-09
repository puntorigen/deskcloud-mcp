"""
Service Layer
=============

Business logic for session management, display management,
filesystem isolation, agent orchestration, and session cleanup.

Multi-Session Architecture:
- DisplayManager: Creates isolated X11 displays per session
- FilesystemManager: Creates isolated filesystems per session (OverlayFS)
- SessionManager: Manages session lifecycle and integrates displays + filesystems
- AgentRunner: Executes agent on session's specific display with isolated filesystem
- SessionCleanupService: Auto-destroys idle sessions (TTL enforcement)
"""

from .agent_runner import AgentRunner
from .display_manager import DisplayManager, display_manager
from .filesystem_manager import FilesystemManager, filesystem_manager
from .session_cleanup import SessionCleanupService, cleanup_service
from .session_manager import SessionManager, session_manager

__all__ = [
    "AgentRunner",
    "DisplayManager",
    "display_manager",
    "FilesystemManager",
    "filesystem_manager",
    "SessionCleanupService",
    "cleanup_service",
    "SessionManager",
    "session_manager",
]

