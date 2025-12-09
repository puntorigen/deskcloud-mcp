"""
Session Cleanup Service
=======================

Background service that automatically destroys idle sessions
to free resources and prevent unbounded growth.

Default Configuration:
- TTL: 1 hour of inactivity
- Check interval: Every 5 minutes

The service runs as an asyncio background task and can be
started/stopped via the application lifespan.

Usage:
    from app.services.session_cleanup import cleanup_service
    
    # In app lifespan
    await cleanup_service.start()
    # ... app runs ...
    await cleanup_service.stop()
"""

import asyncio
import logging
from datetime import datetime, timedelta

from app.config import settings
from app.db.repositories import SessionRepository
from app.db.session import get_db_context
from app.services.session_manager import session_manager
from app.services.display_manager import display_manager
from app.services.filesystem_manager import filesystem_manager

logger = logging.getLogger(__name__)


class SessionCleanupService:
    """
    Background service that destroys idle sessions.
    
    Runs as an asyncio task, checking for expired sessions
    every check_interval seconds and destroying any session
    that hasn't had activity within the TTL period.
    
    Resource Management:
        - Each session uses ~100MB RAM (Xvfb + browser)
        - Cleanup prevents unbounded memory growth
        - Sessions can be manually destroyed via API/MCP
    
    Thread Safety:
        - Uses asyncio for non-blocking operation
        - Safe to run alongside request handling
    """
    
    def __init__(self):
        """Initialize the cleanup service with settings."""
        self.ttl_seconds = settings.session_ttl_seconds
        self.check_interval = settings.cleanup_interval_seconds
        self._task: asyncio.Task | None = None
        self._running = False
    
    async def start(self) -> None:
        """
        Start the cleanup background task.
        
        Safe to call multiple times - will not start duplicate tasks.
        """
        if self._running:
            logger.warning("Cleanup service already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._cleanup_loop())
        
        logger.info(
            f"🧹 Session cleanup started "
            f"(TTL: {self.ttl_seconds}s, interval: {self.check_interval}s)"
        )
    
    async def stop(self) -> None:
        """
        Stop the cleanup background task gracefully.
        
        Waits for the current cleanup cycle to complete.
        """
        if not self._running:
            return
        
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        logger.info("🧹 Session cleanup stopped")
    
    async def _cleanup_loop(self) -> None:
        """
        Main cleanup loop - runs indefinitely.
        
        Sleeps for check_interval, then checks for and destroys
        expired sessions. Handles errors gracefully to prevent
        task termination.
        """
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                
                if self._running:  # Check again after sleep
                    await self._cleanup_expired_sessions()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in cleanup loop: {e}")
                # Continue running despite errors
                await asyncio.sleep(10)
    
    async def _cleanup_expired_sessions(self) -> None:
        """
        Find and destroy sessions that have exceeded TTL.
        
        Uses last_activity timestamp to determine expiration.
        Sessions are archived (soft deleted) and their displays destroyed.
        """
        cutoff = datetime.utcnow() - timedelta(seconds=self.ttl_seconds)
        destroyed_count = 0
        
        try:
            async with get_db_context() as db:
                repo = SessionRepository(db)
                
                # Get sessions that haven't been active since cutoff
                expired = await repo.get_sessions_inactive_since(cutoff)
                
                if not expired:
                    logger.debug("No expired sessions found")
                    return
                
                logger.info(f"Found {len(expired)} expired session(s) to clean up")
                
                for session in expired:
                    try:
                        # Destroy display
                        await display_manager.destroy_display(session.id)
                        
                        # Destroy filesystem
                        if settings.filesystem_isolation_enabled:
                            await filesystem_manager.destroy_filesystem(session.id)
                        
                        # Archive session
                        await repo.delete_session(session.id)
                        
                        destroyed_count += 1
                        logger.info(
                            f"🧹 Auto-destroyed idle session: {session.id} "
                            f"(title: {session.title}, inactive for: "
                            f"{(datetime.utcnow() - session.last_activity).total_seconds():.0f}s)"
                        )
                        
                    except Exception as e:
                        logger.error(
                            f"Failed to destroy session {session.id}: {e}"
                        )
                
                if destroyed_count > 0:
                    logger.info(f"🧹 Cleanup complete: {destroyed_count} session(s) destroyed")
                    
        except Exception as e:
            logger.exception(f"Error during session cleanup: {e}")
    
    async def force_cleanup(self) -> int:
        """
        Force immediate cleanup of expired sessions.
        
        Useful for testing or manual cleanup.
        
        Returns:
            Number of sessions destroyed
        """
        logger.info("Force cleanup triggered")
        
        cutoff = datetime.utcnow() - timedelta(seconds=self.ttl_seconds)
        destroyed_count = 0
        
        async with get_db_context() as db:
            repo = SessionRepository(db)
            expired = await repo.get_sessions_inactive_since(cutoff)
            
            for session in expired:
                try:
                    await display_manager.destroy_display(session.id)
                    if settings.filesystem_isolation_enabled:
                        await filesystem_manager.destroy_filesystem(session.id)
                    await repo.delete_session(session.id)
                    destroyed_count += 1
                except Exception as e:
                    logger.error(f"Failed to destroy session {session.id}: {e}")
        
        return destroyed_count
    
    @property
    def is_running(self) -> bool:
        """Check if the cleanup service is running."""
        return self._running


# =============================================================================
# Global Instance
# =============================================================================

# Singleton cleanup service for use across the application
cleanup_service = SessionCleanupService()
