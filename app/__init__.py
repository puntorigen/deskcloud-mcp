"""
DeskCloud MCP
=============

A FastAPI-based MCP server for AI-controlled virtual desktops,
with real-time streaming, persistence, and VNC/noVNC integration.

Architecture:
- API Layer: FastAPI routes for REST and SSE endpoints
- Service Layer: Session management and agent orchestration  
- Data Layer: SQLAlchemy models with async SQLite/PostgreSQL support
"""

__version__ = "0.1.0"

