"""
FastAPI Application Entry Point
===============================

Main application factory and configuration.
Sets up middleware, routes, lifecycle events, and MCP server.

Usage:
    # Development
    uvicorn app.main:app --reload --port 8000
    
    # Production
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.routes import api_router, llms_router_export
from app.config import settings
from app.db import init_db
from app.services import display_manager, filesystem_manager
from app.services.session_cleanup import cleanup_service

logger = logging.getLogger(__name__)


# =============================================================================
# Application Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize database, start cleanup service, warm up connections
    - Shutdown: Stop cleanup, clean up resources, shutdown displays
    """
    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    
    # Initialize database (creates tables if needed)
    await init_db()
    
    # Log configuration (non-sensitive)
    print(f"📦 API Provider: {settings.api_provider}")
    print(f"🤖 Default Model: {settings.default_model}")
    print(f"🗄️  Database: {settings.database_url.split('://')[0]}")
    
    # Log multi-session architecture info
    print(f"🖥️  Multi-Session Mode: Enabled")
    print(f"   VNC base port: {settings.vnc_base_port}")
    print(f"   noVNC base port: {settings.novnc_base_port}")
    print(f"   Max displays: {settings.max_displays or 'unlimited'}")
    
    # Initialize filesystem isolation
    if settings.filesystem_isolation_enabled:
        print(f"📁 Filesystem Isolation: Enabled")
        await filesystem_manager.initialize_base_filesystem()
        print(f"   Sessions dir: {settings.sessions_dir}")
        print(f"   Base dir: {settings.filesystem_base_dir}")
        print(f"   Quota: {settings.session_disk_quota_mb}MB per session")
    else:
        print(f"📁 Filesystem Isolation: Disabled")
    
    # Log MCP server info
    if settings.mcp_enabled:
        print(f"🔌 MCP Server: Enabled at /mcp")
        print(f"   Session TTL: {settings.session_ttl_seconds}s")
        print(f"   Cleanup interval: {settings.cleanup_interval_seconds}s")
    
    # Check API key
    if settings.anthropic_api_key.get_secret_value():
        print("🔑 API Key: Configured")
    else:
        print("⚠️  API Key: NOT CONFIGURED - Set ANTHROPIC_API_KEY env var")
    
    # Start session cleanup service
    await cleanup_service.start()
    
    print(f"✅ Ready to accept requests on {settings.api_v1_prefix}")
    print(f"📄 LLMs.txt available at /llms.txt")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")
    
    # Stop cleanup service
    await cleanup_service.stop()
    
    # Clean up all active displays
    active_count = display_manager.active_display_count
    if active_count > 0:
        print(f"🖥️  Cleaning up {active_count} active display(s)...")
        await display_manager.shutdown()
        print("   All displays shut down")
    
    # Clean up all active filesystems
    if settings.filesystem_isolation_enabled:
        fs_count = filesystem_manager.active_filesystem_count
        if fs_count > 0:
            print(f"📁 Cleaning up {fs_count} active filesystem(s)...")
            await filesystem_manager.shutdown()
            print("   All filesystems cleaned up")


# =============================================================================
# Rate Limiting
# =============================================================================

limiter = Limiter(key_func=get_remote_address)


# =============================================================================
# Application Factory
# =============================================================================

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns a fully configured app instance with:
    - CORS middleware
    - Rate limiting
    - Exception handlers
    - API routes
    """
    app = FastAPI(
        title=settings.app_name,
        description="""
## Claude Computer Use Backend API

A FastAPI backend for managing Claude Computer Use agent sessions
with real-time streaming, persistent storage, and VNC integration.

### Features
- **Session Management**: Create, list, and manage chat sessions
- **Real-time Streaming**: Server-Sent Events for live agent updates
- **Tool Execution**: Screenshots, mouse clicks, keyboard input
- **Persistence**: SQLite/PostgreSQL storage for session history
- **VNC Integration**: Watch agent actions in real-time

### Quick Start
1. Create a session: `POST /api/v1/sessions`
2. Send a message: `POST /api/v1/sessions/{id}/messages`
3. Stream updates: `GET /api/v1/sessions/{id}/stream` (SSE)
4. Watch via VNC: Open the `vnc_url` from session response

### Authentication
Set your Claude API key via `ANTHROPIC_API_KEY` environment variable.
        """,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # =========================================================================
    # Middleware
    # =========================================================================
    
    # CORS - Allow frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Rate limiting
    app.state.limiter = limiter
    
    # =========================================================================
    # Exception Handlers
    # =========================================================================
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        """Handle rate limit exceeded errors."""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "detail": str(exc.detail),
                "retry_after": getattr(exc, "retry_after", 60),
            },
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Global exception handler for unhandled errors.
        
        In production, this logs the error and returns a generic message.
        In debug mode, includes the full error details.
        """
        if settings.debug:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": type(exc).__name__,
                    "detail": str(exc),
                    "path": str(request.url),
                },
            )
        else:
            # Log error (in production, send to monitoring service)
            print(f"Unhandled error: {type(exc).__name__}: {exc}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "detail": "An unexpected error occurred",
                },
            )
    
    # =========================================================================
    # Routes
    # =========================================================================
    
    # Include all API routes under /api/v1
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    
    # Mount llms.txt at root level (not under /api/v1)
    app.include_router(llms_router_export)
    
    # =========================================================================
    # MCP Server
    # =========================================================================
    
    if settings.mcp_enabled:
        try:
            from app.mcp import create_mcp_app
            
            # Mount MCP server at /mcp
            mcp_app = create_mcp_app()
            app.mount("/mcp", mcp_app)
            
            logger.info("MCP server mounted at /mcp")
        except ImportError as e:
            logger.warning(f"MCP server not available: {e}")
        except Exception as e:
            logger.error(f"Failed to mount MCP server: {e}")
    
    # Root redirect to docs
    @app.get("/", include_in_schema=False)
    async def root():
        """Redirect root to API documentation."""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/docs")
    
    return app


# =============================================================================
# Application Instance
# =============================================================================

# Create the global app instance
app = create_app()


# =============================================================================
# Development Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

