# MCP Server Transformation Plan

**Author:** Pablo Schaffner  
**Date:** December 2025  
**Status:** Proposed Architecture

---

## Executive Summary

### The Goal
Transform the existing Claude Computer Use backend into an **MCP (Model Context Protocol) server** that can be consumed by Cursor IDE, allowing AI assistants to control virtual desktops through standardized tools.

### Key Features
- **MCP Server**: Expose computer-use capabilities as MCP tools
- **Session TTL**: Automatically destroy idle sessions (default: 1 hour)
- **Dual Interface**: Keep REST API alongside MCP for flexibility
- **LLMs.txt**: Machine-readable documentation for AI assistants
- **Render.com Ready**: Single-container deployment

### Architecture Overview

```
                    Cursor IDE
                        │
                        │ MCP Protocol (HTTP)
                        ▼
┌───────────────────────────────────────────────────────────────┐
│                    Render.com Web Service                      │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                    FastAPI Application                    │ │
│  │                                                           │ │
│  │  ┌─────────────┐    ┌──────────────────────────────────┐ │ │
│  │  │  FastMCP    │    │         REST API                 │ │ │
│  │  │  Server     │    │                                  │ │ │
│  │  │  /mcp       │    │  /api/v1/sessions                │ │ │
│  │  │             │    │  /api/v1/health                  │ │ │
│  │  │  Tools:     │    │  /docs                           │ │ │
│  │  │  • create   │    │                                  │ │ │
│  │  │  • execute  │    │  (for direct access, frontend)   │ │ │
│  │  │  • status   │    │                                  │ │ │
│  │  │  • list     │    └──────────────────────────────────┘ │ │
│  │  │  • destroy  │                                        │ │
│  │  │  • screenshot│   ┌──────────────────────────────────┐ │ │
│  │  └─────────────┘    │    Session Cleanup Service       │ │ │
│  │         │           │    (Background Task)             │ │ │
│  │         │           │    • Check every 5 min           │ │ │
│  │         ▼           │    • Destroy sessions > 1hr idle │ │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │            SessionManager + DisplayManager          │ │ │
│  │  │            (Shared by MCP and REST API)            │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                          │                               │ │
│  └──────────────────────────┼───────────────────────────────┘ │
│                              │                                 │
│  ┌──────────────────────────┼───────────────────────────────┐ │
│  │                Virtual Desktops                           │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐                   │ │
│  │  │ Xvfb :1 │  │ Xvfb :2 │  │ Xvfb :3 │  ...              │ │
│  │  │ VNC 5901│  │ VNC 5902│  │ VNC 5903│                   │ │
│  │  │Session 1│  │Session 2│  │Session 3│                   │ │
│  │  └─────────┘  └─────────┘  └─────────┘                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

---

## Table of Contents

1. [What is MCP?](#1-what-is-mcp)
2. [Why Transform to MCP?](#2-why-transform-to-mcp)
3. [MCP Tools Design](#3-mcp-tools-design)
4. [Session TTL & Cleanup](#4-session-ttl--cleanup)
5. [LLMs.txt Documentation](#5-llmstxt-documentation)
6. [Implementation Plan](#6-implementation-plan)
7. [File Changes](#7-file-changes)
8. [Cursor Configuration](#8-cursor-configuration)
9. [Render.com Deployment](#9-rendercom-deployment)
10. [Future: API Key Authentication](#10-future-api-key-authentication)
11. [Future: React Landing Page](#11-future-react-landing-page)
12. [References](#12-references)

---

## 1. What is MCP?

The **Model Context Protocol (MCP)** is an open standard developed by Anthropic that enables AI applications to connect to external tools and data sources in a standardized way.

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Server** | Provides tools, resources, and prompts to clients |
| **Client** | Connects to servers (e.g., Cursor IDE, Claude Desktop) |
| **Tools** | Functions the AI can call (like our computer-use capabilities) |
| **Resources** | Data sources the AI can read |
| **Transport** | Communication method (stdio, HTTP, WebSocket) |

### Why MCP Matters

```
Before MCP:
┌─────────┐     Custom API     ┌─────────┐
│ Cursor  │ ────────────────── │ Service │
└─────────┘                    └─────────┘
     │
     │     Different API       ┌─────────┐
     └──────────────────────── │ Service │
                               └─────────┘

After MCP:
┌─────────┐                    ┌─────────┐
│ Cursor  │ ═══ MCP ═══════════│ Service │
└─────────┘                    └─────────┘
     │                         ┌─────────┐
     └═══════ MCP ═════════════│ Service │
                               └─────────┘
```

MCP provides a **standardized protocol** so AI clients can connect to any MCP-compliant server without custom integration.

---

## 2. Why Transform to MCP?

### Benefits

| Benefit | Description |
|---------|-------------|
| **Cursor Native** | Works seamlessly with Cursor's MCP support |
| **Standardized** | No custom API clients needed |
| **Discoverable** | Tools are self-documenting |
| **Future-Proof** | MCP is gaining wide adoption |

### Use Cases

1. **Cursor IDE Integration**: AI assistant can create sessions and execute computer-use tasks
2. **Claude Desktop**: Same server works with Claude Desktop app
3. **Custom Clients**: Any MCP client can connect

### Example Cursor Workflow

```
User: "Go to amazon.com and search for wireless headphones under $100"

Cursor (via MCP):
1. Calls create_session tool → gets session_id
2. Calls execute_task(session_id, "go to amazon.com...") → agent runs
3. Returns results with screenshots to user
4. Session auto-destroys after 1 hour of inactivity
```

---

## 3. MCP Tools Design

### Tool Overview

| Tool | Description | Long-Running? |
|------|-------------|---------------|
| `create_session` | Create new computer-use session | No |
| `execute_task` | Execute a task in a session | Yes |
| `get_session_status` | Get session status | No |
| `list_sessions` | List all sessions | No |
| `destroy_session` | Destroy a session | No |
| `take_screenshot` | Capture session desktop | No |

### Tool Specifications

#### 1. create_session

Creates a new computer-use session with an isolated virtual desktop.

```python
@mcp.tool()
async def create_session(
    title: str = "Computer Use Session",
    model: str = "claude-sonnet-4-20250514",
    system_prompt_suffix: str = ""
) -> dict:
    """
    Create a new computer-use session with an isolated virtual desktop.
    
    Each session gets its own:
    - X11 display (Xvfb virtual framebuffer)
    - VNC connection for viewing
    - Browser and desktop applications
    
    Args:
        title: Human-readable session title
        model: Claude model to use (default: claude-sonnet-4)
        system_prompt_suffix: Additional instructions for the agent
    
    Returns:
        session_id: Unique identifier for the session
        vnc_url: URL to view the session via noVNC
        status: Current session status
        created_at: Session creation timestamp
    """
```

**Example Response:**
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "vnc_url": "https://your-app.onrender.com/vnc/1/vnc.html",
    "status": "active",
    "created_at": "2025-12-08T10:30:00Z"
}
```

#### 2. execute_task

Executes a task in the session's virtual desktop using the Claude agent.

```python
@mcp.tool()
async def execute_task(
    session_id: str,
    task: str
) -> dict:
    """
    Execute a task in the computer-use session.
    
    The Claude agent will control the virtual desktop to complete the task,
    using tools like:
    - Taking screenshots to understand the screen
    - Moving the mouse and clicking
    - Typing text
    - Running bash commands
    
    This is a long-running operation that may take several minutes
    depending on task complexity.
    
    Args:
        session_id: The session to execute the task in
        task: Natural language description of the task
    
    Returns:
        status: "completed" or "error"
        result: Agent's final response text
        screenshots: List of screenshots taken (base64)
        tool_uses: Summary of tools used during execution
        duration_seconds: How long the task took
    """
```

**Example Response:**
```json
{
    "status": "completed",
    "result": "I found several wireless headphones under $100 on Amazon...",
    "screenshots": ["base64...", "base64..."],
    "tool_uses": [
        {"tool": "screenshot", "count": 5},
        {"tool": "mouse_click", "count": 8},
        {"tool": "keyboard_type", "count": 3}
    ],
    "duration_seconds": 45.2
}
```

#### 3. get_session_status

Get the current status of a session.

```python
@mcp.tool()
def get_session_status(session_id: str) -> dict:
    """
    Get the current status and details of a session.
    
    Args:
        session_id: The session to check
    
    Returns:
        session_id: Session identifier
        status: active, processing, archived, error
        title: Session title
        model: Claude model in use
        vnc_url: URL to view the session
        message_count: Number of messages in history
        last_activity: Timestamp of last activity
        ttl_remaining_seconds: Seconds until auto-destruction
    """
```

#### 4. list_sessions

List all active sessions.

```python
@mcp.tool()
def list_sessions(include_archived: bool = False) -> dict:
    """
    List all computer-use sessions.
    
    Args:
        include_archived: Include destroyed sessions in results
    
    Returns:
        sessions: List of session summaries
        total: Total count
    """
```

#### 5. destroy_session

Destroy a session and free its resources.

```python
@mcp.tool()
async def destroy_session(session_id: str) -> dict:
    """
    Destroy a session and free its resources.
    
    This will:
    - Stop the X11 display and VNC server
    - Archive the session in the database
    - Free memory used by the session
    
    Args:
        session_id: The session to destroy
    
    Returns:
        success: Whether destruction succeeded
        message: Status message
    """
```

#### 6. take_screenshot

Take a screenshot of a session's desktop.

```python
@mcp.tool()
async def take_screenshot(session_id: str) -> dict:
    """
    Take a screenshot of the session's virtual desktop.
    
    Useful for checking the current state without executing a task.
    
    Args:
        session_id: The session to screenshot
    
    Returns:
        image_base64: Screenshot as base64-encoded PNG
        format: Image format (always "png")
        width: Image width in pixels
        height: Image height in pixels
    """
```

---

## 4. Session TTL & Cleanup

### The Problem

Without session cleanup:
- Sessions accumulate over time
- Each session uses ~100MB RAM (Xvfb + applications)
- System eventually runs out of resources
- Abandoned sessions waste resources

### Solution: Automatic TTL

```
┌────────────────────────────────────────────────────────────────┐
│                    Session Lifecycle                            │
│                                                                 │
│  Create ──► Active ──► Idle (no activity) ──► Auto-Destroyed   │
│                │                                                │
│                └──► Processing ──► Active                       │
│                                                                 │
│  Default TTL: 1 hour of inactivity                             │
│  Check interval: Every 5 minutes                                │
└────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# app/services/session_cleanup.py

import asyncio
from datetime import datetime, timedelta
from app.config import settings
from app.services import session_manager
from app.db.session import get_db_context
from app.db.repositories import SessionRepository


class SessionCleanupService:
    """
    Background service that destroys idle sessions.
    
    Runs as an asyncio task, checking for expired sessions
    every CHECK_INTERVAL_SECONDS and destroying any session
    that hasn't had activity in TTL_SECONDS.
    """
    
    def __init__(self):
        self.ttl_seconds = settings.session_ttl_seconds  # Default: 3600 (1 hour)
        self.check_interval = settings.cleanup_interval_seconds  # Default: 300 (5 min)
        self._task: asyncio.Task | None = None
    
    async def start(self):
        """Start the cleanup background task."""
        self._task = asyncio.create_task(self._cleanup_loop())
        print(f"🧹 Session cleanup started (TTL: {self.ttl_seconds}s, interval: {self.check_interval}s)")
    
    async def stop(self):
        """Stop the cleanup background task."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("🧹 Session cleanup stopped")
    
    async def _cleanup_loop(self):
        """Main cleanup loop - runs indefinitely."""
        while True:
            await asyncio.sleep(self.check_interval)
            await self._cleanup_expired_sessions()
    
    async def _cleanup_expired_sessions(self):
        """Find and destroy expired sessions."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.ttl_seconds)
        
        async with get_db_context() as db:
            repo = SessionRepository(db)
            
            # Get sessions that haven't been active since cutoff
            expired = await repo.get_sessions_inactive_since(cutoff)
            
            for session in expired:
                try:
                    await session_manager.delete_session(repo, session.id)
                    print(f"🧹 Auto-destroyed idle session: {session.id}")
                except Exception as e:
                    print(f"⚠️ Failed to destroy session {session.id}: {e}")


# Global instance
cleanup_service = SessionCleanupService()
```

### Configuration

```python
# app/config.py additions

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Session TTL settings
    session_ttl_seconds: int = 3600  # 1 hour default
    cleanup_interval_seconds: int = 300  # 5 minutes
    
    # Future: API key-based extended TTL
    extended_ttl_seconds: int = 86400  # 24 hours for authenticated users
```

### Database Changes

Add `last_activity` field to track when a session was last used:

```python
# app/db/models.py additions

class Session(Base):
    # ... existing fields ...
    
    # Add last_activity tracking
    last_activity: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
```

---

## 5. LLMs.txt Documentation

### What is LLMs.txt?

`llms.txt` is an emerging standard for providing machine-readable documentation that helps LLMs understand how to use a service. Similar to `robots.txt` for search engines, `llms.txt` tells AI assistants what capabilities are available and how to use them.

### Why Include LLMs.txt?

| Benefit | Description |
|---------|-------------|
| **Discoverability** | LLMs can learn about the service automatically |
| **Self-Documenting** | No need to explain the API in every prompt |
| **Best Practices** | Guides LLMs to use the service correctly |
| **Error Prevention** | Helps avoid common mistakes |

### Endpoint

The `llms.txt` file will be served at the root:
```
GET /llms.txt
```

### Sample Content

```txt
# MCP Computer Use Service

> A Model Context Protocol (MCP) server that provides Claude-powered computer use capabilities.
> Each session gets an isolated virtual desktop (Linux) with browser, terminal, and desktop apps.

## MCP Endpoint

Connect via MCP at: /mcp (streamable-http transport)

## Available Tools

### create_session
Create a new computer-use session with isolated virtual desktop.
- title (optional): Human-readable session name
- model (optional): Claude model (default: claude-sonnet-4-20250514)
- Returns: session_id, vnc_url, status

### execute_task
Execute a task in a session. The agent controls the desktop to complete the task.
- session_id (required): Session to use
- task (required): Natural language task description
- Returns: result text, screenshots, tool uses, duration
- Note: This is a long-running operation (may take minutes)

### get_session_status
Get current status of a session.
- session_id (required): Session to check
- Returns: status, last_activity, ttl_remaining

### list_sessions
List all active sessions.
- include_archived (optional): Include destroyed sessions
- Returns: array of sessions

### destroy_session
Destroy a session and free resources.
- session_id (required): Session to destroy
- Returns: success status

### take_screenshot
Capture current state of session's desktop.
- session_id (required): Session to screenshot
- Returns: base64 PNG image

## Session Lifecycle

- Sessions auto-destroy after 1 hour of inactivity
- Use destroy_session to manually clean up
- Each session uses ~100MB RAM

## Example Workflow

1. Call create_session to get a session_id
2. Call execute_task with the session_id and your task
3. Optionally call take_screenshot to see current state
4. Call destroy_session when done (or let it auto-expire)

## Limitations

- Sessions timeout after 1 hour of inactivity
- Long tasks may take several minutes
- Each session is isolated (no shared state)
- Desktop resolution: 1920x1080

## Links

- MCP Endpoint: /mcp
- REST API Docs: /docs
- Health Check: /api/v1/health
```

### Implementation

```python
# app/api/routes/llms.py

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()

LLMS_TXT = """
# MCP Computer Use Service
...
"""  # Full content as above

@router.get("/llms.txt", response_class=PlainTextResponse)
async def get_llms_txt():
    """
    Serve llms.txt for LLM discoverability.
    
    This file helps AI assistants understand how to use
    this MCP server without additional context.
    """
    return LLMS_TXT
```

---

## 6. Implementation Plan

### Phase 1: Core MCP Server (MVP)

**Goal:** Basic MCP server with all tools working

| Task | Effort | Priority |
|------|--------|----------|
| Add `mcp` to requirements.txt | 5 min | P0 |
| Create `app/mcp/server.py` with FastMCP | 1 hour | P0 |
| Implement all 6 tools | 3 hours | P0 |
| Mount MCP at `/mcp` in main.py | 30 min | P0 |
| Create `/llms.txt` endpoint | 30 min | P0 |
| Test with mcp-cli / HTTP client | 1 hour | P0 |

**Total Phase 1:** ~6.5 hours

### Phase 2: Session Cleanup

**Goal:** Automatic destruction of idle sessions

| Task | Effort | Priority |
|------|--------|----------|
| Add `last_activity` to Session model | 30 min | P0 |
| Create SessionCleanupService | 1 hour | P0 |
| Add cleanup settings to config | 15 min | P0 |
| Start cleanup in app lifespan | 15 min | P0 |
| Test cleanup works correctly | 1 hour | P0 |

**Total Phase 2:** ~3 hours

### Phase 3: Production Hardening

**Goal:** Ready for render.com deployment

| Task | Effort | Priority |
|------|--------|----------|
| Add MCP error handling | 1 hour | P1 |
| Add logging for MCP operations | 30 min | P1 |
| Update Dockerfile if needed | 30 min | P1 |
| Create render.yaml | 30 min | P1 |
| Document Cursor configuration | 30 min | P1 |
| End-to-end testing on render | 2 hours | P1 |

**Total Phase 3:** ~5 hours

### Phase 4: API Key Authentication (Future)

**Goal:** Secure access with extended TTL for authenticated users

| Task | Effort | Priority |
|------|--------|----------|
| Design API key system | 1 hour | P2 |
| Implement key validation | 2 hours | P2 |
| Add rate limiting per key | 1 hour | P2 |
| Extended TTL for authenticated | 1 hour | P2 |
| Documentation | 1 hour | P2 |

**Total Phase 4:** ~6 hours

### Total Estimated Effort

| Phase | Effort |
|-------|--------|
| Phase 1: Core MCP Server + llms.txt | 6.5 hours |
| Phase 2: Session Cleanup | 3 hours |
| Phase 3: Production Hardening | 5 hours |
| **Total MVP** | **14.5 hours** |
| Phase 4: API Key (Future) | 6 hours |
| Phase 5: React Landing Page (Future) | 14 hours |

---

## 7. File Changes

### New Files

| File | Purpose |
|------|---------|
| `app/mcp/__init__.py` | MCP module initialization |
| `app/mcp/server.py` | FastMCP server setup |
| `app/mcp/tools.py` | Tool implementations |
| `app/services/session_cleanup.py` | TTL cleanup service |
| `app/api/routes/llms.py` | LLMs.txt endpoint |

### Modified Files

| File | Changes |
|------|---------|
| `app/main.py` | Mount MCP server, add cleanup task |
| `app/config.py` | Add MCP and cleanup settings |
| `app/db/models.py` | Add `last_activity` field |
| `app/services/session_manager.py` | Add `update_activity()` method |
| `requirements.txt` | Add `mcp>=1.0.0` |

### Directory Structure (After)

```
app/
├── __init__.py
├── main.py                    # Modified: mount MCP, serve llms.txt
├── config.py                  # Modified: add settings
├── api/
│   ├── routes/
│   │   ├── llms.py           # NEW: /llms.txt endpoint
│   │   └── ...
│   └── ...
├── mcp/                       # NEW
│   ├── __init__.py
│   ├── server.py             # FastMCP setup
│   └── tools.py              # Tool implementations
├── db/
│   ├── models.py             # Modified: last_activity
│   └── ...
└── services/
    ├── session_manager.py    # Modified: update_activity
    ├── session_cleanup.py    # NEW
    └── ...

# Future (Phase 5)
landing/                       # React landing page
├── package.json
├── vite.config.ts
├── src/
│   └── ...
└── dist/                     # Build output (served by FastAPI)
```

---

## 8. Cursor Configuration

### Setting Up Cursor to Use the MCP Server

#### 1. Create MCP Configuration File

Create `.cursor/mcp.json` in your project or home directory:

```json
{
  "mcpServers": {
    "computer-use": {
      "url": "https://your-app.onrender.com/mcp",
      "transport": "streamable-http"
    }
  }
}
```

#### 2. Alternative: Environment-Based URL

```json
{
  "mcpServers": {
    "computer-use": {
      "url": "${COMPUTER_USE_MCP_URL}",
      "transport": "streamable-http"
    }
  }
}
```

Then set the environment variable:
```bash
export COMPUTER_USE_MCP_URL=https://your-app.onrender.com/mcp
```

#### 3. Local Development

For local testing:
```json
{
  "mcpServers": {
    "computer-use": {
      "url": "http://localhost:8000/mcp",
      "transport": "streamable-http"
    }
  }
}
```

### Using the Tools in Cursor

Once configured, you can ask Cursor to use the tools:

```
User: "Create a computer use session and go to google.com"

Cursor will:
1. Call create_session() → get session_id
2. Call execute_task(session_id, "go to google.com")
3. Return the result with screenshots
```

---

## 9. Render.com Deployment

### Service Configuration

#### render.yaml

```yaml
services:
  - type: web
    name: mcp-computer-use
    env: docker
    dockerfilePath: ./docker/Dockerfile
    dockerContext: .
    healthCheckPath: /api/v1/health
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false  # Set manually in dashboard
      - key: DATABASE_URL
        value: sqlite:///./data/sessions.db
      - key: SESSION_TTL_SECONDS
        value: "3600"
      - key: MCP_ENABLED
        value: "true"
      - key: CORS_ORIGINS
        value: "*"
      - key: DEBUG
        value: "false"
    disk:
      name: data
      mountPath: /app/data
      sizeGB: 1
```

### Resource Recommendations

| Plan | RAM | Sessions | Use Case |
|------|-----|----------|----------|
| Starter | 512MB | 3-4 | Testing |
| Standard | 2GB | 15-20 | Production |
| Pro | 4GB+ | 30-40 | Heavy usage |

Each session uses ~100MB RAM for Xvfb + browser.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | - | Claude API key |
| `DATABASE_URL` | No | sqlite | Database connection |
| `SESSION_TTL_SECONDS` | No | 3600 | Session idle timeout |
| `MCP_ENABLED` | No | true | Enable MCP server |
| `CORS_ORIGINS` | No | * | Allowed origins |

### Deployment Steps

1. **Fork/Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Create Render Web Service**
   - Connect GitHub repo
   - Select Docker environment
   - Configure environment variables

3. **Add Persistent Disk** (for SQLite)
   - Mount at `/app/data`
   - 1GB is sufficient

4. **Deploy**
   - Render auto-deploys on push
   - Check logs for startup

5. **Test MCP Endpoint**
   ```bash
   curl https://your-app.onrender.com/mcp/tools
   ```

---

## 10. Future: API Key Authentication

### The Need

In production, you may want:
- **Rate limiting**: Prevent abuse
- **Extended TTL**: Premium users get longer sessions
- **Usage tracking**: Monitor who uses what
- **Access control**: Restrict to authorized users

### Proposed Design

```
┌─────────────────────────────────────────────────────────────┐
│                    API Key Tiers                             │
│                                                              │
│  Anonymous (no key):                                         │
│  • 1 hour session TTL                                        │
│  • 5 sessions max                                            │
│  • Rate limited: 10 requests/minute                          │
│                                                              │
│  Basic API Key:                                              │
│  • 24 hour session TTL                                       │
│  • 20 sessions max                                           │
│  • Rate limited: 60 requests/minute                          │
│                                                              │
│  Premium API Key:                                            │
│  • 7 day session TTL                                         │
│  • Unlimited sessions                                        │
│  • No rate limiting                                          │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Sketch

```python
# app/mcp/auth.py

from mcp.server.fastmcp import FastMCP
from app.config import settings

# API key validation
def get_api_key_tier(api_key: str | None) -> str:
    if not api_key:
        return "anonymous"
    
    # Check against database or config
    if api_key in settings.premium_api_keys:
        return "premium"
    elif api_key in settings.basic_api_keys:
        return "basic"
    
    return "anonymous"

# Modify tools to respect tier
@mcp.tool()
async def create_session(
    title: str = "Computer Use Session",
    api_key: str = ""  # Optional API key
) -> dict:
    tier = get_api_key_tier(api_key)
    
    # Check session limits
    if tier == "anonymous" and get_session_count() >= 5:
        raise ValueError("Session limit reached. Provide API key for more.")
    
    # Create with appropriate TTL
    session = await session_manager.create_session(
        title=title,
        ttl_seconds=get_ttl_for_tier(tier)
    )
    
    return {...}
```

This is deferred to Phase 4 after the core MCP server is working.

---

## 11. Future: React Landing Page

### Purpose

After the MCP server is tested and working, create a **React-based static landing page** to:
- Promote the service
- Explain how to use it
- Provide setup instructions for Cursor
- Showcase capabilities with demos/screenshots

### Proposed Features

| Feature | Description |
|---------|-------------|
| **Hero Section** | Eye-catching intro with value proposition |
| **How It Works** | Step-by-step visual guide |
| **Live Demo** | Embedded VNC viewer showing a session |
| **Setup Guide** | Copy-paste Cursor configuration |
| **Pricing/Tiers** | Free tier vs. API key tiers |
| **Documentation** | Links to API docs and llms.txt |

### Tech Stack

```
landing/
├── package.json
├── vite.config.ts
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── Hero.tsx
│   │   ├── HowItWorks.tsx
│   │   ├── LiveDemo.tsx
│   │   ├── SetupGuide.tsx
│   │   └── Footer.tsx
│   └── styles/
│       └── globals.css
└── public/
    └── assets/
```

- **Framework**: React + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Deployment**: Render.com static site or same container

### Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│  🖥️  MCP Computer Use                    [Docs] [GitHub] [Try] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│     Let AI Control a Real Computer                              │
│     ─────────────────────────────────                          │
│     Connect Cursor to a virtual desktop powered by Claude.      │
│     Execute any task: browse, code, automate.                   │
│                                                                 │
│              [Get Started]  [Watch Demo]                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│     How It Works                                                │
│     ─────────────                                               │
│                                                                 │
│     1️⃣ Configure        2️⃣ Ask Cursor       3️⃣ Watch It Work   │
│     Add MCP server      "Search Amazon      Agent controls     │
│     to Cursor           for headphones"     the desktop        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│     Live Demo                                                   │
│     ─────────                                                   │
│     ┌─────────────────────────────────────────────────────────┐│
│     │                                                         ││
│     │              [Embedded VNC Viewer]                      ││
│     │                                                         ││
│     └─────────────────────────────────────────────────────────┘│
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│     Quick Setup                                                 │
│     ───────────                                                 │
│     Add to .cursor/mcp.json:                                   │
│     ┌─────────────────────────────────────────────────────────┐│
│     │ {                                                       ││
│     │   "mcpServers": {                                       ││
│     │     "computer-use": {                                   ││
│     │       "url": "https://..."                              ││
│     │     }                                                   ││
│     │   }                                                     ││
│     │ }                                                       ││
│     └─────────────────────────────────────────────────────────┘│
│                            [Copy to Clipboard]                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  © 2025 | GitHub | Documentation | llms.txt                    │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Timeline

| Task | Effort | Priority |
|------|--------|----------|
| Design mockups | 2 hours | P3 |
| React project setup | 1 hour | P3 |
| Hero + How It Works | 3 hours | P3 |
| Live Demo component | 4 hours | P3 |
| Setup Guide (copy-paste) | 1 hour | P3 |
| Responsive styling | 2 hours | P3 |
| Deploy to Render | 1 hour | P3 |

**Total:** ~14 hours (after MCP server is stable)

### Deployment Options

1. **Same Container**: Serve static files from FastAPI
2. **Separate Static Site**: Render.com static site service
3. **Custom Domain**: Optional CNAME for marketing

This is **Phase 5** - only after Phases 1-3 are complete and tested.

---

## 12. References

### MCP Documentation
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/modelcontextprotocol/python-sdk#fastmcp)

### LLMs.txt Standard
- [LLMs.txt Specification](https://llmstxt.org/)
- [LLMs.txt Examples](https://github.com/context7/llms-txt)

### Cursor Configuration
- [Cursor MCP Support](https://docs.cursor.com/advanced/mcp)

### Render.com
- [Docker Deployment](https://render.com/docs/docker)
- [Persistent Disks](https://render.com/docs/disks)

### Related Plans
- [Multi-Session Scaling](./multi_session_scaling.md) - Display isolation architecture

---

## Appendix A: Sample Tool Output

### create_session

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "vnc_url": "https://mcp-computer-use.onrender.com/vnc/1/vnc.html",
  "status": "active",
  "created_at": "2025-12-08T10:30:00Z",
  "ttl_remaining_seconds": 3600
}
```

### execute_task

```json
{
  "status": "completed",
  "result": "I successfully searched for wireless headphones on Amazon. Here's what I found:\n\n1. Sony WH-CH520 - $49.99\n2. JBL Tune 510BT - $39.95\n3. Anker Soundcore Q20 - $59.99\n\nAll are under $100 and have good reviews.",
  "screenshots": [
    "data:image/png;base64,iVBORw0KGgo...",
    "data:image/png;base64,iVBORw0KGgo..."
  ],
  "tool_uses": [
    {"tool": "screenshot", "count": 5},
    {"tool": "mouse_click", "count": 12},
    {"tool": "keyboard_type", "count": 4}
  ],
  "duration_seconds": 67.3
}
```

### get_session_status

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "title": "Amazon Search",
  "model": "claude-sonnet-4-20250514",
  "vnc_url": "https://mcp-computer-use.onrender.com/vnc/1/vnc.html",
  "message_count": 5,
  "last_activity": "2025-12-08T10:45:00Z",
  "ttl_remaining_seconds": 2700
}
```

---

## Appendix B: Quick Start Commands

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with Docker
docker-compose up --build

# Test MCP endpoint
curl http://localhost:8000/mcp

# List tools
curl http://localhost:8000/mcp/tools
```

### Testing with mcp-cli

```bash
# Install mcp-cli
pip install mcp-cli

# Connect to local server
mcp connect http://localhost:8000/mcp

# List tools
mcp tools

# Create session
mcp call create_session '{"title": "Test Session"}'

# Execute task
mcp call execute_task '{"session_id": "...", "task": "Open Firefox"}'
```

---

*This document provides the complete plan for transforming the Claude Computer Use backend into an MCP server. Implementation should follow the phases outlined, with Phase 1 and 2 being the MVP and Phase 3-4 for production readiness.*
