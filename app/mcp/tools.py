"""
MCP Tool Implementations
========================

Defines all MCP tools for computer-use functionality:
- create_session: Create new computer-use session
- execute_task: Execute a task in a session
- get_session_status: Get session status
- list_sessions: List all sessions  
- destroy_session: Destroy a session
- take_screenshot: Capture session desktop

Each tool wraps the existing SessionManager functionality
to expose it via the MCP protocol.
"""

import asyncio
import base64
import logging
import subprocess
import time
from datetime import datetime, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from app.config import settings
from app.db.repositories import SessionRepository
from app.db.session import get_db_context
from app.services import session_manager
from app.services.display_manager import display_manager

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP) -> None:
    """
    Register all computer-use tools with the MCP server.
    
    Args:
        mcp: FastMCP server instance to register tools on
    """
    
    # =========================================================================
    # Tool: create_session
    # =========================================================================
    
    @mcp.tool()
    async def create_session(
        title: str = "Computer Use Session",
        model: str | None = None,
        system_prompt_suffix: str = "",
    ) -> dict[str, Any]:
        """
        Create a new computer-use session with an isolated virtual desktop.
        
        Each session gets its own:
        - X11 display (Xvfb virtual framebuffer)
        - VNC connection for viewing the desktop
        - Browser and desktop applications
        
        Sessions automatically expire after 1 hour of inactivity.
        
        Args:
            title: Human-readable session title (default: "Computer Use Session")
            model: Claude model to use (default: claude-sonnet-4-5-20250929)
            system_prompt_suffix: Additional instructions appended to the system prompt
        
        Returns:
            session_id: Unique identifier for the session
            vnc_url: URL to view the session via noVNC web interface
            status: Current session status (always "active" for new sessions)
            created_at: Session creation timestamp (ISO format)
            ttl_remaining_seconds: Seconds until auto-destruction (3600 for new sessions)
        """
        logger.info(f"MCP: Creating session with title='{title}'")
        
        model = model or settings.default_model
        
        async with get_db_context() as db:
            repo = SessionRepository(db)
            
            session = await session_manager.create_session(
                repo=repo,
                title=title,
                model=model,
                system_prompt_suffix=system_prompt_suffix or None,
            )
            
            # Get VNC URL
            vnc_url = display_manager.get_vnc_url(session.id)
            
            logger.info(f"MCP: Session created: {session.id}")
            
            return {
                "session_id": session.id,
                "vnc_url": vnc_url or "Display not available",
                "status": session.status.value,
                "created_at": session.created_at.isoformat(),
                "ttl_remaining_seconds": settings.session_ttl_seconds,
            }
    
    # =========================================================================
    # Tool: execute_task
    # =========================================================================
    
    @mcp.tool()
    async def execute_task(
        session_id: str,
        task: str,
    ) -> dict[str, Any]:
        """
        Execute a task in the computer-use session.
        
        The Claude agent will control the virtual desktop to complete the task,
        using tools like:
        - Taking screenshots to understand the screen
        - Moving the mouse and clicking on elements
        - Typing text with the keyboard
        - Running bash commands in the terminal
        
        This is a LONG-RUNNING operation that may take several minutes
        depending on task complexity. The agent will work autonomously
        until the task is complete or an error occurs.
        
        Args:
            session_id: The session to execute the task in (from create_session)
            task: Natural language description of what you want the agent to do
        
        Returns:
            status: "completed" or "error"
            result: Agent's final response text describing what was done
            screenshots: List of final screenshots (base64 PNG)
            tool_uses: Summary of tools used during execution
            duration_seconds: How long the task took
            error: Error message if status is "error"
        """
        logger.info(f"MCP: Executing task in session {session_id}: {task[:100]}...")
        
        start_time = time.time()
        
        async with get_db_context() as db:
            repo = SessionRepository(db)
            
            # Get session
            session = await repo.get_session(session_id, include_messages=True)
            if not session:
                logger.error(f"MCP: Session not found: {session_id}")
                return {
                    "status": "error",
                    "error": f"Session not found: {session_id}",
                    "result": None,
                    "screenshots": [],
                    "tool_uses": [],
                    "duration_seconds": 0,
                }
            
            # Check session is active
            if session.status.value == "archived":
                return {
                    "status": "error",
                    "error": "Session has been archived/destroyed",
                    "result": None,
                    "screenshots": [],
                    "tool_uses": [],
                    "duration_seconds": 0,
                }
            
            try:
                # Send message and get event queue
                message_id, event_queue = await session_manager.send_message(
                    repo=repo,
                    session=session,
                    content=task,
                )
                
                # Collect events until completion
                result_text = ""
                screenshots = []
                tool_uses = []
                
                while True:
                    try:
                        event = await asyncio.wait_for(
                            event_queue.get(),
                            timeout=300.0,  # 5 minute timeout per event
                        )
                        
                        if event.type.value == "text":
                            result_text += event.data.get("content", "")
                            
                        elif event.type.value == "tool_result":
                            # Capture screenshots from tool results
                            tool_data = event.data
                            if tool_data.get("tool_name") == "screenshot":
                                if "output" in tool_data:
                                    screenshots.append(tool_data["output"])
                            tool_uses.append({
                                "tool": tool_data.get("tool_name", "unknown"),
                                "success": not tool_data.get("is_error", False),
                            })
                            
                        elif event.type.value == "tool_use":
                            # Track tool usage
                            pass
                            
                        elif event.type.value == "message_complete":
                            break
                            
                        elif event.type.value == "error":
                            error_msg = event.data.get("error", "Unknown error")
                            logger.error(f"MCP: Task error: {error_msg}")
                            return {
                                "status": "error",
                                "error": error_msg,
                                "result": result_text or None,
                                "screenshots": screenshots[-3:],  # Last 3
                                "tool_uses": _summarize_tool_uses(tool_uses),
                                "duration_seconds": round(time.time() - start_time, 1),
                            }
                            
                    except asyncio.TimeoutError:
                        logger.error(f"MCP: Task timed out for session {session_id}")
                        return {
                            "status": "error",
                            "error": "Task timed out (5 minutes without activity)",
                            "result": result_text or None,
                            "screenshots": screenshots[-3:],
                            "tool_uses": _summarize_tool_uses(tool_uses),
                            "duration_seconds": round(time.time() - start_time, 1),
                        }
                
                duration = round(time.time() - start_time, 1)
                logger.info(f"MCP: Task completed in {duration}s for session {session_id}")
                
                return {
                    "status": "completed",
                    "result": result_text,
                    "screenshots": screenshots[-3:],  # Return last 3 screenshots
                    "tool_uses": _summarize_tool_uses(tool_uses),
                    "duration_seconds": duration,
                }
                
            except ValueError as e:
                logger.error(f"MCP: Task error: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "result": None,
                    "screenshots": [],
                    "tool_uses": [],
                    "duration_seconds": round(time.time() - start_time, 1),
                }
            except Exception as e:
                logger.exception(f"MCP: Unexpected error in execute_task: {e}")
                return {
                    "status": "error",
                    "error": f"Unexpected error: {str(e)}",
                    "result": None,
                    "screenshots": [],
                    "tool_uses": [],
                    "duration_seconds": round(time.time() - start_time, 1),
                }
    
    # =========================================================================
    # Tool: get_session_status
    # =========================================================================
    
    @mcp.tool()
    async def get_session_status(session_id: str) -> dict[str, Any]:
        """
        Get the current status and details of a session.
        
        Use this to check if a session is still active, see how many
        messages have been exchanged, and check remaining TTL.
        
        Args:
            session_id: The session to check (from create_session)
        
        Returns:
            session_id: Session identifier
            status: Current status (active, processing, completed, error, archived)
            title: Session title
            model: Claude model in use
            vnc_url: URL to view the session desktop
            message_count: Number of messages in conversation history
            last_activity: Timestamp of last activity (ISO format)
            ttl_remaining_seconds: Seconds until auto-destruction
            error: Error message if session not found
        """
        logger.debug(f"MCP: Getting status for session {session_id}")
        
        async with get_db_context() as db:
            repo = SessionRepository(db)
            
            session = await repo.get_session(session_id, include_messages=True)
            if not session:
                return {
                    "error": f"Session not found: {session_id}",
                    "session_id": session_id,
                    "status": None,
                }
            
            # Calculate TTL remaining
            last_activity = session.last_activity if hasattr(session, 'last_activity') and session.last_activity else session.updated_at
            ttl_remaining = max(0, settings.session_ttl_seconds - (datetime.utcnow() - last_activity).total_seconds())
            
            vnc_url = display_manager.get_vnc_url(session_id)
            
            return {
                "session_id": session.id,
                "status": session.status.value,
                "title": session.title,
                "model": session.model,
                "vnc_url": vnc_url or "Display not available",
                "message_count": len(session.messages),
                "last_activity": last_activity.isoformat(),
                "ttl_remaining_seconds": int(ttl_remaining),
            }
    
    # =========================================================================
    # Tool: list_sessions (DISABLED - requires authentication)
    # =========================================================================
    # 
    # NOTE: list_sessions is intentionally not exposed via MCP for security.
    # Listing all sessions would expose information about other users' sessions.
    # This will be enabled in Phase 4 when API key authentication is added,
    # and will only return sessions belonging to the authenticated user.
    #
    # For now, users should track their own session_ids returned by create_session.
    # Admins can use the REST API with future authentication.
    
    # =========================================================================
    # Tool: destroy_session
    # =========================================================================
    
    @mcp.tool()
    async def destroy_session(session_id: str) -> dict[str, Any]:
        """
        Destroy a session and free its resources.
        
        This will:
        - Stop the X11 display and VNC server
        - Archive the session in the database (chat history preserved)
        - Free memory used by the session (~100MB)
        
        Sessions also auto-destroy after 1 hour of inactivity, so this
        is optional but recommended when you're done with a session.
        
        Args:
            session_id: The session to destroy (from create_session)
        
        Returns:
            success: Whether destruction succeeded
            message: Status message
        """
        logger.info(f"MCP: Destroying session {session_id}")
        
        async with get_db_context() as db:
            repo = SessionRepository(db)
            
            session = await repo.get_session(session_id, include_messages=False)
            if not session:
                return {
                    "success": False,
                    "message": f"Session not found: {session_id}",
                }
            
            if session.status.value == "archived":
                return {
                    "success": False,
                    "message": "Session already archived/destroyed",
                }
            
            try:
                await session_manager.delete_session(repo, session_id)
                
                logger.info(f"MCP: Session destroyed: {session_id}")
                
                return {
                    "success": True,
                    "message": f"Session {session_id} destroyed successfully",
                }
                
            except Exception as e:
                logger.error(f"MCP: Failed to destroy session: {e}")
                return {
                    "success": False,
                    "message": f"Failed to destroy session: {str(e)}",
                }
    
    # =========================================================================
    # Tool: take_screenshot
    # =========================================================================
    
    @mcp.tool()
    async def take_screenshot(session_id: str) -> dict[str, Any]:
        """
        Take a screenshot of the session's virtual desktop.
        
        Useful for checking the current state of a session without
        executing a task. Returns the screenshot as base64-encoded PNG.
        
        Args:
            session_id: The session to screenshot (from create_session)
        
        Returns:
            image_base64: Screenshot as base64-encoded PNG data
            format: Image format (always "png")
            width: Image width in pixels
            height: Image height in pixels
            error: Error message if screenshot failed
        """
        logger.debug(f"MCP: Taking screenshot for session {session_id}")
        
        # Get display info
        display_info = display_manager.get_display_info(session_id)
        if not display_info:
            return {
                "error": f"No display found for session: {session_id}",
                "image_base64": None,
                "format": None,
                "width": 0,
                "height": 0,
            }
        
        display_env = f":{display_info.display_num}"
        
        try:
            # Use import-window-id to capture the screen
            result = subprocess.run(
                ["import", "-window", "root", "-display", display_env, "png:-"],
                capture_output=True,
                timeout=10,
            )
            
            if result.returncode != 0:
                # Fallback to scrot if import fails
                result = subprocess.run(
                    ["scrot", "-d", display_env, "-o", "-"],
                    capture_output=True,
                    timeout=10,
                    env={"DISPLAY": display_env},
                )
            
            if result.returncode == 0 and result.stdout:
                image_data = base64.b64encode(result.stdout).decode("utf-8")
                
                return {
                    "image_base64": image_data,
                    "format": "png",
                    "width": settings.screen_width,
                    "height": settings.screen_height,
                }
            else:
                error = result.stderr.decode("utf-8") if result.stderr else "Unknown error"
                logger.error(f"MCP: Screenshot failed: {error}")
                return {
                    "error": f"Screenshot failed: {error}",
                    "image_base64": None,
                    "format": None,
                    "width": 0,
                    "height": 0,
                }
                
        except subprocess.TimeoutExpired:
            return {
                "error": "Screenshot timed out",
                "image_base64": None,
                "format": None,
                "width": 0,
                "height": 0,
            }
        except Exception as e:
            logger.exception(f"MCP: Screenshot error: {e}")
            return {
                "error": f"Screenshot error: {str(e)}",
                "image_base64": None,
                "format": None,
                "width": 0,
                "height": 0,
            }


# =============================================================================
# Helper Functions
# =============================================================================

def _summarize_tool_uses(tool_uses: list[dict]) -> list[dict]:
    """
    Summarize tool uses into counts by tool name.
    
    Args:
        tool_uses: List of individual tool use records
    
    Returns:
        List of {tool, count, success_count} summaries
    """
    from collections import defaultdict
    
    counts = defaultdict(lambda: {"count": 0, "success": 0})
    
    for use in tool_uses:
        tool_name = use.get("tool", "unknown")
        counts[tool_name]["count"] += 1
        if use.get("success", True):
            counts[tool_name]["success"] += 1
    
    return [
        {"tool": name, "count": data["count"], "success_count": data["success"]}
        for name, data in counts.items()
    ]
