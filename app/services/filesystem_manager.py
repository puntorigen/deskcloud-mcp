"""
Filesystem Manager Service
==========================

Manages OverlayFS-based filesystem isolation for sessions.
Each session gets a copy-on-write view of a shared base filesystem.

Architecture:
    Base Layer (read-only, shared):
        /sessions/base/
        ├── home/user/        # Default home directory
        ├── tmp/              # Empty temp directory
        └── .config/          # Default app configs

    Per-Session Upper Layer (writable):
        /sessions/active/{session_id}/
        ├── upper/            # CoW changes go here
        ├── work/             # OverlayFS workdir (required)
        └── merged/           # Mount point (what session sees)

Benefits:
    - Zero disk cost until files are written (copy-on-write)
    - Each session has isolated /home, /tmp, downloads
    - Fast cleanup: just rm -rf the session directory
    - Integrates with CRIU snapshots for persistence

Requirements:
    OverlayFS is a KERNEL FEATURE (not a package to install).
    Any Linux host running Docker already has it - Docker itself uses OverlayFS!
    
    The only requirement is PERMISSIONS in docker-compose.yml:
        cap_add:
          - SYS_ADMIN
        security_opt:
          - apparmor:unconfined

The entrypoint.sh script verifies mount permissions on startup
and exits with a clear error if CAP_SYS_ADMIN is missing.
"""

import asyncio
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FilesystemInfo:
    """
    Information about an active session filesystem.
    
    Attributes:
        session_id: Session identifier
        home_path: Path to isolated home directory
        tmp_path: Path to isolated temp directory
        merged_root: Path to the merged overlay mount point
        upper_path: Path to the upper (writable) layer
        is_mounted: Whether the overlay is currently mounted
    """
    session_id: str
    home_path: str
    tmp_path: str
    merged_root: str
    upper_path: str
    is_mounted: bool = False
    
    def to_env_dict(self) -> dict[str, str]:
        """
        Get environment variables for processes running in this filesystem.
        
        Returns:
            Dict with HOME, TMPDIR, XDG_* variables set to isolated paths
        """
        return {
            "HOME": self.home_path,
            "TMPDIR": self.tmp_path,
            "XDG_CONFIG_HOME": f"{self.home_path}/.config",
            "XDG_DATA_HOME": f"{self.home_path}/.local/share",
            "XDG_CACHE_HOME": f"{self.home_path}/.cache",
            "XDG_RUNTIME_DIR": self.tmp_path,
        }


class FilesystemManager:
    """
    Manages OverlayFS-based filesystem isolation for sessions.
    
    Provides each session with an isolated filesystem view where:
    - Reads go to the shared base layer (OS, apps, default configs)
    - Writes go to a per-session upper layer (copy-on-write)
    - The merged view appears as a complete filesystem
    
    This enables:
    - File isolation between sessions (downloads, configs)
    - Browser profile isolation (cookies, history)
    - Efficient storage (only changed files stored per session)
    
    IMPORTANT: OverlayFS is REQUIRED. The container must have:
    - CAP_SYS_ADMIN capability
    - apparmor:unconfined security option
    
    The entrypoint.sh verifies this on container startup.
    
    Usage:
        filesystem_manager = FilesystemManager()
        
        # Create isolated filesystem for session
        fs_info = await filesystem_manager.create_filesystem("sess_abc123")
        
        # Get environment variables for agent
        env = fs_info.to_env_dict()
        
        # Cleanup when session ends
        await filesystem_manager.destroy_filesystem("sess_abc123")
    """
    
    _instance: Optional["FilesystemManager"] = None
    
    def __new__(cls) -> "FilesystemManager":
        """Singleton pattern - only one FilesystemManager instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the filesystem manager."""
        if self._initialized:
            return
        
        # Directory paths from settings
        self.sessions_dir = Path(settings.sessions_dir)
        self.base_dir = Path(settings.filesystem_base_dir)
        self.active_dir = self.sessions_dir / "active"
        self.snapshots_dir = self.sessions_dir / "snapshots"
        
        # Track active filesystems
        self._filesystems: dict[str, FilesystemInfo] = {}
        
        # Lock for thread-safe access
        self._lock = asyncio.Lock()
        
        # Check if OverlayFS is available
        self._overlayfs_available: bool | None = None
        
        self._initialized = True
        logger.info("FilesystemManager initialized")
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    async def create_filesystem(self, session_id: str) -> FilesystemInfo:
        """
        Create an isolated filesystem for a session using OverlayFS.
        
        OverlayFS is required for proper session isolation. The container
        must have CAP_SYS_ADMIN capability for mount operations.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            FilesystemInfo with paths and environment
        
        Raises:
            RuntimeError: If OverlayFS mount fails
        """
        async with self._lock:
            # Check if session already has a filesystem
            if session_id in self._filesystems:
                logger.info(f"Filesystem already exists for session {session_id}")
                return self._filesystems[session_id]
            
            logger.info(f"Creating filesystem for session {session_id}")
            
            try:
                # Get paths for this session
                paths = self._get_session_paths(session_id)
                
                # Create directories
                for name, path in paths.items():
                    path.mkdir(parents=True, exist_ok=True)
                
                # Verify OverlayFS is available (permissions issue, not installation)
                if not await self._is_overlayfs_available():
                    raise RuntimeError(
                        "Cannot mount OverlayFS - this is a PERMISSIONS issue. "
                        "OverlayFS is a kernel feature, not a package to install. "
                        "Ensure docker-compose.yml has: cap_add: [SYS_ADMIN] and "
                        "security_opt: [apparmor:unconfined]"
                    )
                
                # Mount OverlayFS (required, no fallback)
                await self._mount_overlay(session_id, paths)
                logger.info(f"OverlayFS mounted for session {session_id}")
                
                # Create filesystem info
                fs_info = FilesystemInfo(
                    session_id=session_id,
                    home_path=str(paths["merged"] / "home" / "user"),
                    tmp_path=str(paths["merged"] / "tmp"),
                    merged_root=str(paths["merged"]),
                    upper_path=str(paths["upper"]),
                    is_mounted=True,
                )
                
                # Track the filesystem
                self._filesystems[session_id] = fs_info
                
                logger.info(f"Filesystem created for session {session_id}")
                
                return fs_info
                
            except Exception as e:
                # Clean up on failure
                try:
                    if paths["root"].exists():
                        shutil.rmtree(paths["root"])
                except Exception:
                    pass
                logger.error(f"Failed to create filesystem for {session_id}: {e}")
                raise RuntimeError(f"Failed to create filesystem: {e}")
    
    async def destroy_filesystem(self, session_id: str) -> bool:
        """
        Unmount and remove session filesystem.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if filesystem was destroyed, False if not found
        """
        async with self._lock:
            if session_id not in self._filesystems:
                logger.warning(f"No filesystem found for session {session_id}")
                return False
            
            fs_info = self._filesystems[session_id]
            paths = self._get_session_paths(session_id)
            
            logger.info(f"Destroying filesystem for session {session_id}")
            
            try:
                # Unmount overlay if mounted
                if fs_info.is_mounted:
                    await self._unmount_overlay(paths["merged"])
                
                # Remove session directory
                if paths["root"].exists():
                    shutil.rmtree(paths["root"])
                
                # Remove from tracking
                del self._filesystems[session_id]
                
                logger.info(f"Filesystem destroyed for session {session_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error destroying filesystem for {session_id}: {e}")
                # Still remove from tracking
                del self._filesystems[session_id]
                return False
    
    def get_filesystem_info(self, session_id: str) -> FilesystemInfo | None:
        """
        Get filesystem information for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            FilesystemInfo or None if not found
        """
        return self._filesystems.get(session_id)
    
    def get_filesystem_env(self, session_id: str) -> dict[str, str] | None:
        """
        Get environment variables for running processes in isolated filesystem.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dict with environment variables, or None if no filesystem
        """
        fs_info = self._filesystems.get(session_id)
        if not fs_info:
            return None
        return fs_info.to_env_dict()
    
    def has_filesystem(self, session_id: str) -> bool:
        """Check if a session has an active filesystem."""
        return session_id in self._filesystems
    
    def get_disk_usage(self, session_id: str) -> dict | None:
        """
        Get disk usage for a session's filesystem.
        
        Only counts the upper layer (session-specific changes).
        
        Returns:
            Dict with size_bytes and size_mb, or None if not found
        """
        if session_id not in self._filesystems:
            return None
        
        paths = self._get_session_paths(session_id)
        upper_path = paths["upper"]
        
        if not upper_path.exists():
            return {"size_bytes": 0, "size_mb": 0.0}
        
        total_size = sum(
            f.stat().st_size
            for f in upper_path.rglob("*")
            if f.is_file()
        )
        
        return {
            "session_id": session_id,
            "size_bytes": total_size,
            "size_mb": round(total_size / (1024 * 1024), 2),
        }
    
    @property
    def active_filesystem_count(self) -> int:
        """Get the number of active filesystems."""
        return len(self._filesystems)
    
    async def shutdown(self) -> None:
        """
        Shutdown all filesystems gracefully.
        
        Should be called when the application is shutting down.
        """
        logger.info("Shutting down all filesystems...")
        
        session_ids = list(self._filesystems.keys())
        for session_id in session_ids:
            await self.destroy_filesystem(session_id)
        
        logger.info("All filesystems shut down")
    
    # =========================================================================
    # Snapshot Integration (for CRIU)
    # =========================================================================
    
    async def archive_filesystem(
        self,
        session_id: str,
        compress: bool = True
    ) -> dict:
        """
        Archive session filesystem for snapshot storage.
        
        Used before CRIU suspend to preserve filesystem state.
        
        Args:
            session_id: Session identifier
            compress: Whether to compress the archive
        
        Returns:
            Dict with archive path and size
        """
        if session_id not in self._filesystems:
            raise ValueError(f"No filesystem for session {session_id}")
        
        fs_info = self._filesystems[session_id]
        paths = self._get_session_paths(session_id)
        snapshot_dir = self.snapshots_dir / session_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        archive_name = "filesystem.tar.zst" if compress else "filesystem.tar"
        archive_path = snapshot_dir / archive_name
        
        # Unmount before archiving
        if fs_info.is_mounted:
            await self._unmount_overlay(paths["merged"])
        
        # Archive upper layer (only the changes)
        if compress:
            cmd = ["tar", "-I", "zstd", "-cf", str(archive_path),
                   "-C", str(paths["upper"]), "."]
        else:
            cmd = ["tar", "-cf", str(archive_path),
                   "-C", str(paths["upper"]), "."]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"Failed to archive filesystem: {stderr.decode()}")
        
        # Clean up active directory
        shutil.rmtree(paths["root"])
        
        # Update tracking
        del self._filesystems[session_id]
        
        size = archive_path.stat().st_size
        return {
            "session_id": session_id,
            "archive_path": str(archive_path),
            "size_bytes": size,
            "size_mb": round(size / (1024 * 1024), 2),
            "compressed": compress,
        }
    
    async def restore_filesystem(self, session_id: str) -> FilesystemInfo:
        """
        Restore session filesystem from archive.
        
        Used before CRIU restore to restore filesystem state.
        
        Args:
            session_id: Session identifier
        
        Returns:
            FilesystemInfo for the restored filesystem
        """
        snapshot_dir = self.snapshots_dir / session_id
        paths = self._get_session_paths(session_id)
        
        # Find archive
        archive_path = None
        for name in ["filesystem.tar.zst", "filesystem.tar"]:
            if (snapshot_dir / name).exists():
                archive_path = snapshot_dir / name
                break
        
        if not archive_path:
            raise FileNotFoundError(f"No filesystem archive for {session_id}")
        
        # Create directories
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)
        
        # Extract upper layer
        if ".zst" in archive_path.name:
            cmd = ["tar", "-I", "zstd", "-xf", str(archive_path),
                   "-C", str(paths["upper"])]
        else:
            cmd = ["tar", "-xf", str(archive_path),
                   "-C", str(paths["upper"])]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"Failed to restore filesystem: {stderr.decode()}")
        
        # Mount overlay (required - permissions issue if fails)
        if not await self._is_overlayfs_available():
            raise RuntimeError(
                "Cannot mount OverlayFS for restore - PERMISSIONS issue. "
                "Check docker-compose.yml has cap_add: [SYS_ADMIN]"
            )
        
        await self._mount_overlay(session_id, paths)
        
        # Create filesystem info
        fs_info = FilesystemInfo(
            session_id=session_id,
            home_path=str(paths["merged"] / "home" / "user"),
            tmp_path=str(paths["merged"] / "tmp"),
            merged_root=str(paths["merged"]),
            upper_path=str(paths["upper"]),
            is_mounted=True,
        )
        
        self._filesystems[session_id] = fs_info
        return fs_info
    
    # =========================================================================
    # Initialization
    # =========================================================================
    
    async def initialize_base_filesystem(self) -> None:
        """
        Initialize the base filesystem template.
        
        Creates the shared read-only base layer with:
        - Default home directory structure
        - Default application configs
        - Empty temp directory
        
        Should be called during application startup.
        """
        logger.info("Initializing base filesystem...")
        
        # Create base directories
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.active_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Create base layer structure
        base_home = self.base_dir / "home" / "user"
        base_tmp = self.base_dir / "tmp"
        
        base_home.mkdir(parents=True, exist_ok=True)
        base_tmp.mkdir(parents=True, exist_ok=True)
        
        # Create common directories
        for subdir in [".config", ".local/share", ".cache", "Desktop", "Downloads"]:
            (base_home / subdir).mkdir(parents=True, exist_ok=True)
        
        # Set permissions
        os.chmod(base_tmp, 0o1777)  # Sticky bit for /tmp
        
        logger.info(f"Base filesystem initialized at {self.base_dir}")
    
    # =========================================================================
    # Private Methods
    # =========================================================================
    
    def _get_session_paths(self, session_id: str) -> dict[str, Path]:
        """Get all paths for a session."""
        session_root = self.active_dir / session_id
        return {
            "root": session_root,
            "upper": session_root / "upper",
            "work": session_root / "work",
            "merged": session_root / "merged",
        }
    
    async def _is_overlayfs_available(self) -> bool:
        """Check if OverlayFS is available on this system."""
        if self._overlayfs_available is not None:
            return self._overlayfs_available
        
        # Check if we can mount overlayfs
        try:
            # Try to read /proc/filesystems to check for overlay support
            proc = await asyncio.create_subprocess_exec(
                "grep", "-q", "overlay", "/proc/filesystems",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.communicate()
            
            if proc.returncode != 0:
                self._overlayfs_available = False
                return False
            
            # Check if we have CAP_SYS_ADMIN (needed for mount)
            # Try a test mount in a temp location
            test_dir = Path("/tmp/.overlayfs_test")
            test_dir.mkdir(parents=True, exist_ok=True)
            
            for subdir in ["lower", "upper", "work", "merged"]:
                (test_dir / subdir).mkdir(exist_ok=True)
            
            proc = await asyncio.create_subprocess_exec(
                "mount", "-t", "overlay", "overlay",
                "-o", f"lowerdir={test_dir}/lower,"
                      f"upperdir={test_dir}/upper,"
                      f"workdir={test_dir}/work",
                str(test_dir / "merged"),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            if proc.returncode == 0:
                # Cleanup test mount
                await asyncio.create_subprocess_exec(
                    "umount", str(test_dir / "merged")
                )
                shutil.rmtree(test_dir)
                self._overlayfs_available = True
                logger.info("OverlayFS is available")
            else:
                shutil.rmtree(test_dir, ignore_errors=True)
                self._overlayfs_available = False
                logger.info("OverlayFS not available (insufficient privileges)")
            
            return self._overlayfs_available
            
        except Exception as e:
            logger.warning(f"Error checking OverlayFS availability: {e}")
            self._overlayfs_available = False
            return False
    
    async def _mount_overlay(
        self,
        session_id: str,
        paths: dict[str, Path]
    ) -> None:
        """Mount OverlayFS for a session."""
        mount_cmd = [
            "mount", "-t", "overlay", "overlay",
            "-o", f"lowerdir={self.base_dir},"
                  f"upperdir={paths['upper']},"
                  f"workdir={paths['work']}",
            str(paths["merged"])
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *mount_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"OverlayFS mount failed: {stderr.decode()}")
    
    async def _unmount_overlay(self, merged_path: Path) -> None:
        """Unmount an overlay filesystem."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "umount", str(merged_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
        except Exception as e:
            logger.warning(f"Error unmounting overlay: {e}")
    


# =============================================================================
# Global Instance
# =============================================================================

# Singleton filesystem manager for use across the application
filesystem_manager = FilesystemManager()
