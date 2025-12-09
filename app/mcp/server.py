"""
MCP Server Configuration
========================

Sets up the FastMCP server instance and registers all computer-use tools.
This server can be mounted to the main FastAPI application.

Usage:
    from app.mcp import create_mcp_app
    
    # Mount to FastAPI
    app.mount("/mcp", create_mcp_app())
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

from .tools import register_tools

logger = logging.getLogger(__name__)

# =============================================================================
# MCP Server Instance
# =============================================================================

# Create the FastMCP server
mcp_server = FastMCP(
    "MCP Computer Use",
    json_response=True,
    stateless_http=True,  # Stateless for better scalability
)

# Register all tools
register_tools(mcp_server)

logger.info("MCP Server initialized with tools: %s", [
    "create_session",
    "execute_task", 
    "get_session_status",
    "destroy_session",
    "take_screenshot",
])


# =============================================================================
# App Factory
# =============================================================================

def create_mcp_app():
    """
    Create a Starlette app for the MCP server.
    
    This can be mounted to the main FastAPI application:
        app.mount("/mcp", create_mcp_app())
    
    Returns:
        Starlette ASGI application for MCP
    """
    return mcp_server.streamable_http_app()
