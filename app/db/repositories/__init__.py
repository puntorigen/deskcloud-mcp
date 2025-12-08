"""
Data Access Layer (Repository Pattern)
======================================

Provides clean abstraction over database operations.
"""

from .session_repo import SessionRepository

__all__ = ["SessionRepository"]

