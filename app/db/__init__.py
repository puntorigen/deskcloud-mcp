"""
Database Layer
==============

Provides async SQLAlchemy models and session management.
Supports both SQLite (development) and PostgreSQL (production).
"""

from .models import Base, Message, Session, SessionStatus
from .session import get_db, init_db

__all__ = [
    "Base",
    "Session",
    "SessionStatus", 
    "Message",
    "get_db",
    "init_db",
]

