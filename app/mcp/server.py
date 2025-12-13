"""
MCP Server Configuration
========================

Sets up the FastMCP server instance and registers all MCP tools.
This server can be mounted to the main FastAPI application.

BYOK (Bring Your Own Key) Support:
    Users can provide their own Anthropic API key via HTTP header:
    - Header: X-Anthropic-API-Key
    
    This allows free orchestration while users pay for their own API usage.
    
    MCP Client Config (Cursor):
    {
        "mcpServers": {
            "deskcloud-mcp": {
                "url": "http://localhost:8000/mcp",
                "headers": {
                    "X-Anthropic-API-Key": "sk-ant-..."
                }
            }
        }
    }

Usage:
    from app.mcp import create_mcp_app
    
    # Mount to FastAPI
    app.mount("/mcp", create_mcp_app())
"""

import logging

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .context import set_current_api_key_with_reset

logger = logging.getLogger(__name__)


# =============================================================================
# MCP Server Instance
# =============================================================================

# Create the FastMCP server
mcp_server = FastMCP(
    "DeskCloud MCP",
    json_response=True,
    stateless_http=True,  # Stateless for better scalability
)

# Register all tools (import here to avoid circular dependency)
from .tools import register_tools
register_tools(mcp_server)

logger.info("MCP Server initialized with tools: %s", [
    "create_session",
    "execute_task", 
    "get_session_status",
    "destroy_session",
    "take_screenshot",
])


# =============================================================================
# BYOK Middleware
# =============================================================================

class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract API key from request headers.
    
    Supports BYOK (Bring Your Own Key) where users provide their
    Anthropic API key via the X-Anthropic-API-Key header.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extract API key from header
        api_key = request.headers.get("X-Anthropic-API-Key")
        
        if api_key:
            logger.debug("BYOK: API key provided via header")
        
        token = set_current_api_key_with_reset(api_key)
        
        try:
            response = await call_next(request)
            return response
        finally:
            token.reset()


# =============================================================================
# App Factory
# =============================================================================

def create_mcp_app():
    """
    Create a Starlette app for the MCP server with BYOK support.
    
    This can be mounted to the main FastAPI application:
        app.mount("/mcp", create_mcp_app())
    
    The app includes middleware to extract API keys from headers,
    enabling BYOK (Bring Your Own Key) functionality.
    
    Returns:
        Starlette ASGI application for MCP
    """
    # Get the base MCP app
    base_app = mcp_server.streamable_http_app()
    
    # Wrap with our middleware
    base_app.add_middleware(APIKeyMiddleware)
    
    return base_app
