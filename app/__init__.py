"""
Claude Computer Use Backend
===========================

A FastAPI-based backend for managing Claude Computer Use agent sessions
with real-time streaming, persistent storage, and VNC integration.

Architecture:
- API Layer: FastAPI routes for REST and SSE endpoints
- Service Layer: Session management and agent orchestration  
- Data Layer: SQLAlchemy models with async SQLite/PostgreSQL support
"""

__version__ = "1.0.0"

