"""
Display Manager Service
=======================

Manages multiple X11 virtual displays within a single container.
Each session gets its own isolated Xvfb display with dedicated VNC server.

This enables concurrent sessions with isolated visual state:
- Each session has its own DISPLAY=:N
- Each session has its own VNC port (5900 + N)
- Each session has its own window manager instance
- Browser tabs, forms, and desktop state are isolated per session

Architecture:
    Session 1 → Xvfb :1 → x11vnc :5901 → noVNC :6081
    Session 2 → Xvfb :2 → x11vnc :5902 → noVNC :6082
    Session 3 → Xvfb :3 → x11vnc :5903 → noVNC :6083
    ...
"""

import asyncio
import logging
import os
import shutil
import signal
import subprocess
from dataclasses import dataclass, field
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DisplayInfo:
    """
    Information about an active display for a session.
    
    Attributes:
        display_num: X11 display number (e.g., 1 for :1)
        vnc_port: VNC server port (5900 + display_num)
        novnc_port: noVNC web port (6080 + display_num)
        xvfb_pid: Process ID of Xvfb server
        vnc_pid: Process ID of x11vnc server
        wm_pid: Process ID of window manager
        novnc_pid: Process ID of noVNC websocket proxy
    """
    display_num: int
    vnc_port: int
    novnc_port: int
    xvfb_pid: int | None = None
    vnc_pid: int | None = None
    wm_pid: int | None = None
    novnc_pid: int | None = None
    
    @property
    def display_env(self) -> str:
        """Get DISPLAY environment variable value."""
        return f":{self.display_num}"
    
    @property
    def vnc_url(self) -> str:
        """Get the noVNC web URL for this display."""
        # Use hostname from settings or localhost
        host = settings.vnc_host
        return f"http://{host}:{self.novnc_port}/vnc.html"


class DisplayManager:
    """
    Manages multiple X11 virtual displays within a single container.
    
    Thread-safe singleton that tracks active displays and their processes.
    Each session gets an isolated X11 display with its own VNC server.
    
    Resource Usage:
        - Xvfb: ~10-20MB RAM per display
        - x11vnc: ~5-10MB RAM per display
        - Window manager: ~30-50MB RAM per display
        - Total: ~50-100MB RAM per session
    
    Usage:
        display_manager = DisplayManager()
        
        # Create display for new session
        display_info = await display_manager.create_display("sess_abc123")
        
        # Get display environment for agent
        env = display_manager.get_display_env("sess_abc123")
        
        # Get VNC URL for frontend
        vnc_url = display_manager.get_vnc_url("sess_abc123")
        
        # Cleanup when session ends
        await display_manager.destroy_display("sess_abc123")
    """
    
    _instance: Optional["DisplayManager"] = None
    
    def __new__(cls) -> "DisplayManager":
        """Singleton pattern - only one DisplayManager instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the display manager."""
        if self._initialized:
            return
            
        # Track displays by session_id
        self._displays: dict[str, DisplayInfo] = {}
        
        # Track used display numbers to avoid conflicts
        self._used_display_nums: set[int] = set()
        
        # Next display number to assign (starts at 1)
        self._next_display_num: int = 1
        
        # Lock for thread-safe access
        self._lock = asyncio.Lock()
        
        # Mark as initialized
        self._initialized = True
        
        logger.info("DisplayManager initialized")
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    async def create_display(self, session_id: str) -> DisplayInfo:
        """
        Create a new virtual X11 display for a session.
        
        Starts:
        1. Xvfb - Virtual framebuffer X server
        2. Window manager (mutter) - Desktop environment
        3. x11vnc - VNC server
        4. noVNC - Web-based VNC client proxy
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            DisplayInfo with connection details
        
        Raises:
            RuntimeError: If display creation fails
        """
        async with self._lock:
            # Check if session already has a display
            if session_id in self._displays:
                logger.info(f"Display already exists for session {session_id}")
                return self._displays[session_id]
            
            # Allocate display number
            display_num = self._allocate_display_num()
            vnc_port = settings.vnc_base_port + display_num
            novnc_port = settings.novnc_base_port + display_num
            
            logger.info(f"Creating display :{display_num} for session {session_id}")
            
            try:
                # Start Xvfb
                xvfb_pid = await self._start_xvfb(display_num)
                
                # Wait for X server to be ready
                await self._wait_for_display(display_num)
                
                # Start window manager
                wm_pid = await self._start_window_manager(display_num)
                
                # Start VNC server
                vnc_pid = await self._start_vnc(display_num, vnc_port)
                
                # Start noVNC proxy
                novnc_pid = await self._start_novnc(vnc_port, novnc_port)
                
                # Create display info
                display_info = DisplayInfo(
                    display_num=display_num,
                    vnc_port=vnc_port,
                    novnc_port=novnc_port,
                    xvfb_pid=xvfb_pid,
                    vnc_pid=vnc_pid,
                    wm_pid=wm_pid,
                    novnc_pid=novnc_pid,
                )
                
                # Track the display
                self._displays[session_id] = display_info
                
                logger.info(
                    f"Display :{display_num} created for session {session_id} "
                    f"(VNC port: {vnc_port}, noVNC port: {novnc_port})"
                )
                
                return display_info
                
            except Exception as e:
                # Cleanup on failure
                self._release_display_num(display_num)
                logger.error(f"Failed to create display for session {session_id}: {e}")
                raise RuntimeError(f"Failed to create display: {e}")
    
    async def destroy_display(self, session_id: str) -> bool:
        """
        Stop all processes for a session's display and clean up.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if display was destroyed, False if not found
        """
        async with self._lock:
            if session_id not in self._displays:
                logger.warning(f"No display found for session {session_id}")
                return False
            
            display_info = self._displays[session_id]
            display_num = display_info.display_num
            
            logger.info(f"Destroying display :{display_num} for session {session_id}")
            
            # Kill processes in reverse order
            for pid_attr in ["novnc_pid", "vnc_pid", "wm_pid", "xvfb_pid"]:
                pid = getattr(display_info, pid_attr)
                if pid:
                    await self._kill_process(pid, pid_attr)
            
            # Remove tracking
            del self._displays[session_id]
            self._release_display_num(display_num)
            
            # Clean up X11 lock files
            self._cleanup_x11_locks(display_num)
            
            logger.info(f"Display :{display_num} destroyed for session {session_id}")
            return True
    
    def get_display_env(self, session_id: str) -> dict[str, str] | None:
        """
        Get environment variables for running processes on this display.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dict with DISPLAY variable, or None if no display
        """
        display_info = self._displays.get(session_id)
        if not display_info:
            return None
        
        return {"DISPLAY": display_info.display_env}
    
    def get_display_info(self, session_id: str) -> DisplayInfo | None:
        """
        Get full display information for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            DisplayInfo or None if no display exists
        """
        return self._displays.get(session_id)
    
    def get_vnc_url(self, session_id: str) -> str | None:
        """
        Get the VNC viewer URL for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            noVNC web URL or None if no display
        """
        display_info = self._displays.get(session_id)
        if not display_info:
            return None
        return display_info.vnc_url
    
    def has_display(self, session_id: str) -> bool:
        """Check if a session has an active display."""
        return session_id in self._displays
    
    @property
    def active_display_count(self) -> int:
        """Get the number of active displays."""
        return len(self._displays)
    
    async def shutdown(self) -> None:
        """
        Shutdown all displays gracefully.
        
        Should be called when the application is shutting down.
        """
        logger.info("Shutting down all displays...")
        
        session_ids = list(self._displays.keys())
        for session_id in session_ids:
            await self.destroy_display(session_id)
        
        logger.info("All displays shut down")
    
    # =========================================================================
    # Private Methods - Display Number Management
    # =========================================================================
    
    def _allocate_display_num(self) -> int:
        """Allocate the next available display number."""
        while self._next_display_num in self._used_display_nums:
            self._next_display_num += 1
        
        display_num = self._next_display_num
        self._used_display_nums.add(display_num)
        self._next_display_num += 1
        
        return display_num
    
    def _release_display_num(self, display_num: int) -> None:
        """Release a display number for reuse."""
        self._used_display_nums.discard(display_num)
    
    # =========================================================================
    # Private Methods - Process Management
    # =========================================================================
    
    async def _start_xvfb(self, display_num: int) -> int:
        """
        Start Xvfb virtual framebuffer.
        
        Returns:
            Process ID
        """
        width = settings.screen_width
        height = settings.screen_height
        
        cmd = [
            "Xvfb",
            f":{display_num}",
            "-screen", "0", f"{width}x{height}x24",
            "-ac",  # Disable access control
            "-nolisten", "tcp",  # Security: no TCP connections
        ]
        
        logger.debug(f"Starting Xvfb: {' '.join(cmd)}")
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        return proc.pid
    
    async def _wait_for_display(self, display_num: int, timeout: float = 5.0) -> None:
        """
        Wait for X display to be ready.
        
        Args:
            display_num: Display number to wait for
            timeout: Maximum seconds to wait
        
        Raises:
            RuntimeError: If display not ready within timeout
        """
        import time
        
        display = f":{display_num}"
        start = time.time()
        
        while time.time() - start < timeout:
            # Try to connect to the display
            result = subprocess.run(
                ["xdpyinfo", "-display", display],
                capture_output=True,
                timeout=1,
            )
            
            if result.returncode == 0:
                logger.debug(f"Display {display} is ready")
                return
            
            await asyncio.sleep(0.1)
        
        raise RuntimeError(f"Display {display} not ready after {timeout}s")
    
    async def _start_window_manager(self, display_num: int) -> int:
        """
        Start window manager for the display.
        
        Uses mutter for GNOME-compatible desktop or falls back to simpler WMs.
        
        Returns:
            Process ID
        """
        display = f":{display_num}"
        env = {**os.environ, "DISPLAY": display}
        
        # Try mutter first (GNOME), then fallback to simpler WMs
        wm_commands = [
            ["mutter", "--replace", "--sm-disable"],
            ["openbox"],
            ["fluxbox"],
        ]
        
        for cmd in wm_commands:
            if shutil.which(cmd[0]):
                logger.debug(f"Starting {cmd[0]} for display {display}")
                
                proc = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                
                # Give WM time to start
                await asyncio.sleep(0.5)
                
                return proc.pid
        
        logger.warning("No window manager found, continuing without one")
        return 0
    
    async def _start_vnc(self, display_num: int, vnc_port: int) -> int:
        """
        Start x11vnc VNC server for the display.
        
        Returns:
            Process ID
        """
        display = f":{display_num}"
        
        cmd = [
            "x11vnc",
            "-display", display,
            "-rfbport", str(vnc_port),
            "-forever",       # Don't exit after first client disconnects
            "-shared",        # Allow multiple VNC clients
            "-nopw",          # No password (auth handled at API level)
            "-xkb",           # Use XKEYBOARD extension
            "-noxrecord",     # Disable RECORD extension (not needed)
            "-noxfixes",      # Disable XFIXES (performance)
            "-noxdamage",     # Disable XDAMAGE (compatibility)
            "-wait", "5",     # Polling interval (ms)
            "-defer", "5",    # Defer updates (ms)
        ]
        
        logger.debug(f"Starting x11vnc on port {vnc_port}: {' '.join(cmd)}")
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        # Give VNC server time to start
        await asyncio.sleep(0.3)
        
        return proc.pid
    
    async def _start_novnc(self, vnc_port: int, novnc_port: int) -> int:
        """
        Start noVNC websocket proxy.
        
        noVNC provides web-based VNC access via WebSocket.
        
        Returns:
            Process ID
        """
        # Find noVNC launch script
        novnc_paths = [
            "/opt/noVNC/utils/novnc_proxy",
            "/usr/share/novnc/utils/novnc_proxy",
            "/usr/share/novnc/utils/launch.sh",
            "novnc_proxy",
        ]
        
        novnc_cmd = None
        for path in novnc_paths:
            if shutil.which(path) or os.path.exists(path):
                novnc_cmd = path
                break
        
        if not novnc_cmd:
            logger.warning("noVNC not found, VNC web access will not be available")
            return 0
        
        cmd = [
            novnc_cmd,
            "--listen", str(novnc_port),
            "--vnc", f"localhost:{vnc_port}",
        ]
        
        logger.debug(f"Starting noVNC on port {novnc_port}: {' '.join(cmd)}")
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        # Give noVNC time to start
        await asyncio.sleep(0.3)
        
        return proc.pid
    
    async def _kill_process(self, pid: int, name: str) -> None:
        """
        Kill a process gracefully.
        
        First tries SIGTERM, then SIGKILL after timeout.
        """
        try:
            os.kill(pid, signal.SIGTERM)
            logger.debug(f"Sent SIGTERM to {name} (pid {pid})")
            
            # Wait briefly for graceful shutdown
            for _ in range(10):
                try:
                    os.kill(pid, 0)  # Check if still running
                    await asyncio.sleep(0.1)
                except ProcessLookupError:
                    return  # Process ended
            
            # Force kill if still running
            os.kill(pid, signal.SIGKILL)
            logger.debug(f"Sent SIGKILL to {name} (pid {pid})")
            
        except ProcessLookupError:
            pass  # Process already ended
        except Exception as e:
            logger.warning(f"Error killing {name} (pid {pid}): {e}")
    
    def _cleanup_x11_locks(self, display_num: int) -> None:
        """
        Clean up X11 lock files for a display.
        
        Xvfb creates lock files that can prevent reusing display numbers.
        """
        lock_files = [
            f"/tmp/.X{display_num}-lock",
            f"/tmp/.X11-unix/X{display_num}",
        ]
        
        for lock_file in lock_files:
            try:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
                    logger.debug(f"Removed lock file: {lock_file}")
            except Exception as e:
                logger.warning(f"Could not remove {lock_file}: {e}")


# =============================================================================
# Global Instance
# =============================================================================

# Singleton display manager for use across the application
display_manager = DisplayManager()

