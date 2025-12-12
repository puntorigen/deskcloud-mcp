# Session Video Recording: FFmpeg-Based Screen Capture

> ⚠️ **Start Here**: Read [`MASTER_ROADMAP.md`](./MASTER_ROADMAP.md) first for project context and overview.

**Author:** Pablo Schaffner  
**Date:** December 2025  
**Status:** Proposed Feature  
**Priority**: 🟡 Medium - Phase 9 (after Connect Agent)  
**Depends on:** [Multi-Session Scaling](./multi_session_scaling.md)

---

## Executive Summary

### The Problem

Users cannot review what happened during a session after it completes. While chat history preserves text and tool calls, **the visual context is lost**. This makes:
- Debugging agent behavior difficult
- Demonstrating capabilities challenging
- Auditing session activity impossible

### The Solution

Use **FFmpeg x11grab** to record each session's X11 display as video, then upload to **Cloudflare R2** for permanent, cost-effective storage:

```
SESSION LIFECYCLE                    LOCAL                    CLOUD (R2)
┌─────────────────────────┐         ┌──────────────┐         ┌──────────────────┐
│  Create Session         │         │              │         │                  │
│  ├── Start Xvfb :1      │         │              │         │  Cloudflare R2   │
│  ├── Start VNC          │         │              │         │  ┌────────────┐  │
│  └── Start FFmpeg ──────┼────────►│ /tmp/rec/    │         │  │ recordings/│  │
│                         │         │              │         │  │            │  │
│  Execute Task(s)        │         │ sess_abc.mp4 │         │  │ 2025/12/10/│  │
│  ├── Browser opens      │  ───────┼───► (temp)   │         │  │  sess_abc  │  │
│  ├── Agent clicks       │         │              │         │  │  sess_def  │  │
│  └── Forms filled       │         │              │         │  │  sess_ghi  │  │
│                         │         │              │         │  └────────────┘  │
│  Destroy Session        │         │              │  upload │                  │
│  ├── Stop FFmpeg ───────┼────────►│ Finalized ───┼────────►│  Permanent ✓     │
│  └── Delete local ──────┼────────►│ Deleted      │         │  $0.015/GB/mo    │
└─────────────────────────┘         └──────────────┘         └──────────────────┘
                                                                      │
                                                              signed URL (1h)
                                                                      ▼
                                                             ┌──────────────────┐
                                                             │  User Download   │
                                                             │  (via CDN)       │
                                                             │  $0 egress!      │
                                                             └──────────────────┘
```

### Key Benefits

| Benefit | Description |
|---------|-------------|
| **Full Replay** | Watch exactly what the agent did, step by step |
| **Debugging** | Identify why agent made certain decisions |
| **Demos** | Share session recordings for marketing/training |
| **Compliance** | Audit trail of automated actions |
| **Quality Assurance** | Review agent performance over time |

---

## Table of Contents

1. [Why Record Sessions?](#1-why-record-sessions)
2. [Technical Approach](#2-technical-approach)
3. [Architecture Integration](#3-architecture-integration)
4. [Implementation](#4-implementation)
5. [API & MCP Tools](#5-api--mcp-tools)
6. [Cloud Storage (Cloudflare R2)](#6-cloud-storage-cloudflare-r2)
7. [Storage Lifecycle & Cleanup](#7-storage-lifecycle--cleanup)
8. [Configuration Options](#8-configuration-options)
9. [Resource Impact](#9-resource-impact)
10. [Security Considerations](#10-security-considerations)
11. [Dashboard & Frontend Integration](#11-dashboard--frontend-integration)
12. [Future Enhancements](#12-future-enhancements)
13. [Implementation Plan](#13-implementation-plan)
14. [References](#14-references)

---

## 1. Why Record Sessions?

### 1.1 Current Limitations

Today, sessions provide:
- ✅ Chat history (text messages)
- ✅ Tool use records (what tools were called)
- ✅ Screenshots (static snapshots via `take_screenshot`)
- ❌ **Video of actual session activity**

This means users cannot:
- See the agent's visual context between screenshots
- Watch transitions and animations
- Review mouse movements and timing
- Understand why the agent made certain decisions

### 1.2 Use Cases

#### Debugging & Development
```
Developer: "The agent clicked the wrong button. Why?"
→ Watch recording, see that button text was ambiguous
→ Improve system prompt for similar situations
```

#### Customer Demos
```
Sales: "Here's a recording of our AI agent booking a flight"
→ Share MP4 showing smooth, capable automation
```

#### Compliance & Audit
```
Enterprise: "We need proof the agent only accessed authorized data"
→ Review recordings for compliance verification
```

#### Training Data
```
ML Team: "Which sessions had issues we can learn from?"
→ Review recordings of error cases
```

---

## 2. Technical Approach

### 2.1 Why FFmpeg x11grab?

We evaluated three approaches:

| Approach | Efficiency | Quality | Complexity | Recommended |
|----------|------------|---------|------------|-------------|
| **FFmpeg x11grab** | ⭐⭐⭐ High | ⭐⭐⭐ High | ⭐⭐⭐ Low | ✅ Yes |
| VNC Recording | ⭐⭐ Medium | ⭐⭐ Medium | ⭐⭐ Medium | ❌ No |
| Screenshot Stitching | ⭐ Low | ⭐ Low | ⭐⭐ Medium | ❌ No |

**FFmpeg x11grab** wins because:
- Direct framebuffer access (no VNC latency)
- Industry-standard, battle-tested
- Configurable quality/size tradeoffs
- Low CPU overhead with proper settings
- Already available in most Linux images

### 2.2 How x11grab Works

FFmpeg's x11grab device captures directly from the X11 display server:

```
┌─────────────────────────────────────────────────────────────┐
│                     X11 Display Server                       │
│                         (Xvfb :1)                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Framebuffer                        │   │
│  │                   1024x768x24                        │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │           Rendered Desktop                    │  │   │
│  │  │  ┌─────────────────────────────────────────┐ │  │   │
│  │  │  │  Firefox Window                         │ │  │   │
│  │  │  │  ┌─────────────────────────────────┐   │ │  │   │
│  │  │  │  │  Web Page Content               │   │ │  │   │
│  │  │  │  └─────────────────────────────────┘   │ │  │   │
│  │  │  └─────────────────────────────────────────┘ │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│           │                                                  │
│           │ FFmpeg reads directly                           │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ffmpeg -f x11grab -i :1 → H.264 → output.mp4       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Recording Command

```bash
ffmpeg \
  -f x11grab \                        # Capture from X11
  -video_size 1024x768 \              # Screen resolution
  -framerate 15 \                     # Frames per second
  -i :1 \                             # Display to capture
  -c:v libx264 \                      # H.264 codec
  -preset ultrafast \                 # Minimize CPU usage
  -crf 28 \                           # Quality (lower = better)
  -pix_fmt yuv420p \                  # Compatibility
  /recordings/sess_abc123.mp4         # Output file
```

#### Parameter Explanation

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `-f x11grab` | - | Use X11 capture device |
| `-video_size` | 1024x768 | Match Xvfb resolution |
| `-framerate` | 15 | Balance smoothness vs size |
| `-i :N` | :1, :2, etc | Display number |
| `-c:v libx264` | - | H.264 for compatibility |
| `-preset ultrafast` | - | Minimize CPU at cost of compression |
| `-crf` | 28 | Constant Rate Factor (18-28 good range) |
| `-pix_fmt yuv420p` | - | Maximum player compatibility |

---

## 3. Architecture Integration

### 3.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Docker Container                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI + MCP Server (:8000)                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                    ┌─────────┴─────────┐                                │
│                    │  Session Manager  │                                │
│                    └─────────┬─────────┘                                │
│                              │                                           │
│  ┌───────────────────────────┼───────────────────────────┐              │
│  │                           │                           │              │
│  ▼                           ▼                           ▼              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ Display Manager │  │Filesystem Manager│  │Recording Manager│  NEW    │
│  └────────┬────────┘  └─────────────────┘  └────────┬────────┘         │
│           │                                          │                  │
│           │ creates                                  │ records          │
│           ▼                                          ▼                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │   Session 1         │   Session 2         │   Session 3         │   │
│  │   Xvfb :1           │   Xvfb :2           │   Xvfb :3           │   │
│  │   VNC :5901         │   VNC :5902         │   VNC :5903         │   │
│  │   FFmpeg → .mp4     │   FFmpeg → .mp4     │   FFmpeg → .mp4     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  /sessions/recordings/                                           │   │
│  │    ├── sess_abc123.mp4                                          │   │
│  │    ├── sess_def456.mp4                                          │   │
│  │    └── sess_ghi789.mp4                                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Integration with Session Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Session Lifecycle                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  POST /sessions                                                          │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  1. Create database record                                       │   │
│  │  2. Create filesystem (OverlayFS)                                │   │
│  │  3. Create display (Xvfb + VNC + WM)                            │   │
│  │  4. Start recording (FFmpeg) ◄─────────────────── NEW           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                  │
│       ▼                                                                  │
│  Session Active (recording in progress)                                  │
│       │                                                                  │
│       ▼                                                                  │
│  DELETE /sessions/{id}                                                   │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  1. Stop recording (SIGINT → finalize) ◄────────── NEW          │   │
│  │  2. Destroy display (kill Xvfb + VNC + WM)                      │   │
│  │  3. Destroy filesystem (unmount OverlayFS)                      │   │
│  │  4. Archive database record                                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│       │                                                                  │
│       ▼                                                                  │
│  Recording available at /recordings/sess_xxx.mp4                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Implementation

### 4.1 New File Structure

```
app/
├── services/
│   ├── display_manager.py       # Existing
│   ├── filesystem_manager.py    # Existing
│   ├── session_manager.py       # Modified
│   ├── session_cleanup.py       # Existing
│   └── recording_manager.py     # NEW
├── api/
│   └── routes/
│       ├── sessions.py          # Modified (add recording endpoints)
│       └── recordings.py        # NEW (optional, for dedicated routes)
└── mcp/
    └── tools.py                 # Modified (add recording tools)
```

### 4.2 RecordingManager Service

```python
# app/services/recording_manager.py
"""
Recording Manager Service
=========================

Records session activity as video files using FFmpeg x11grab.
Each session's display is recorded from creation to destruction.

Architecture:
    Session 1 → Xvfb :1 → FFmpeg → /recordings/sess_abc123.mp4
    Session 2 → Xvfb :2 → FFmpeg → /recordings/sess_def456.mp4
    Session 3 → Xvfb :3 → FFmpeg → /recordings/sess_ghi789.mp4

Output Format:
    - Container: MP4
    - Codec: H.264 (libx264)
    - Resolution: Matches display (default 1024x768)
    - Framerate: 15 fps (configurable)
    - Quality: CRF 28 (configurable, 18-28 recommended)
"""

import asyncio
import logging
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RecordingInfo:
    """
    Information about an active recording.
    
    Attributes:
        session_id: Session being recorded
        display_num: X11 display number (:1, :2, etc)
        output_path: Path to output video file
        ffmpeg_pid: Process ID of ffmpeg
        started_at: Unix timestamp when recording started
    """
    session_id: str
    display_num: int
    output_path: Path
    ffmpeg_pid: Optional[int] = None
    started_at: Optional[float] = None
    
    @property
    def duration_seconds(self) -> float:
        """Get recording duration in seconds."""
        if self.started_at is None:
            return 0.0
        return time.time() - self.started_at
    
    @property
    def is_active(self) -> bool:
        """Check if recording is still active."""
        if self.ffmpeg_pid is None:
            return False
        try:
            os.kill(self.ffmpeg_pid, 0)
            return True
        except ProcessLookupError:
            return False


class RecordingManager:
    """
    Manages video recording of session displays.
    
    Thread-safe singleton that tracks active recordings and their FFmpeg processes.
    Each session can optionally have its display recorded as an MP4 video.
    
    Resource Usage:
        - FFmpeg: ~30-50MB RAM per recording
        - CPU: ~5-10% per recording (with ultrafast preset)
        - Disk: ~5-10 MB/min at 15fps CRF 28
    
    Usage:
        recording_manager = RecordingManager()
        
        # Start recording for session
        info = await recording_manager.start_recording("sess_abc", 1)
        
        # Later, stop recording
        video_path = await recording_manager.stop_recording("sess_abc")
        
        # Check recording status
        info = recording_manager.get_recording_info("sess_abc")
    """
    
    _instance: Optional["RecordingManager"] = None
    
    def __new__(cls) -> "RecordingManager":
        """Singleton pattern - only one RecordingManager instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the recording manager."""
        if self._initialized:
            return
        
        # Track recordings by session_id
        self._recordings: dict[str, RecordingInfo] = {}
        
        # Lock for thread-safe access
        self._lock = asyncio.Lock()
        
        # Ensure recordings directory exists
        self._recordings_dir = Path(settings.recordings_dir)
        self._recordings_dir.mkdir(parents=True, exist_ok=True)
        
        # Mark as initialized
        self._initialized = True
        
        logger.info(f"RecordingManager initialized (dir: {self._recordings_dir})")
    
    # =========================================================================
    # Security: Session ID Validation
    # =========================================================================
    
    def _validate_session_id(self, session_id: str) -> None:
        """
        Validate session_id to prevent path traversal attacks.
        
        Valid: sess_abc123, session_def456
        Invalid: ../etc/passwd, sess_abc/../other, /etc/passwd
        
        Raises:
            ValueError: If session_id is invalid
        """
        import re
        
        # Only allow alphanumeric, underscore, hyphen
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            raise ValueError(f"Invalid session_id format: {session_id}")
        
        # Ensure no path components (defense in depth)
        if '/' in session_id or '\\' in session_id or '..' in session_id:
            raise ValueError(f"Invalid session_id: path traversal detected")
    
    def _get_safe_recording_path(self, session_id: str) -> Path:
        """
        Get recording path with security validation.
        
        Ensures the path is within the recordings directory.
        
        Args:
            session_id: Session identifier (will be validated)
        
        Returns:
            Safe path within recordings directory
        
        Raises:
            ValueError: If path would escape recordings directory
        """
        self._validate_session_id(session_id)
        
        path = self._recordings_dir / f"{session_id}.mp4"
        
        # Ensure path is within recordings directory (defense in depth)
        try:
            path.resolve().relative_to(self._recordings_dir.resolve())
        except ValueError:
            raise ValueError(f"Path escape attempt detected: {session_id}")
        
        return path
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    async def start_recording(
        self,
        session_id: str,
        display_num: int,
        fps: int | None = None,
        crf: int | None = None,
    ) -> RecordingInfo:
        """
        Start recording a session's display.
        
        Launches FFmpeg to capture the X11 display and encode to MP4.
        Recording continues until stop_recording is called.
        
        Args:
            session_id: Session identifier
            display_num: X11 display number (1, 2, etc)
            fps: Frames per second (default from settings)
            crf: Constant Rate Factor for quality (default from settings)
        
        Returns:
            RecordingInfo with process details
        
        Raises:
            ValueError: If session_id is invalid
            RuntimeError: If recording fails to start
        """
        # Validate session_id (security: prevent path traversal)
        self._validate_session_id(session_id)
        
        async with self._lock:
            # Check if already recording
            if session_id in self._recordings:
                logger.info(f"Recording already exists for session {session_id}")
                return self._recordings[session_id]
            
            # Use defaults from settings
            fps = fps or settings.recording_fps
            crf = crf or settings.recording_crf
            
            # Output path (uses safe path generation)
            output_path = self._get_safe_recording_path(session_id)
            display = f":{display_num}"
            
            logger.info(f"Starting recording for session {session_id} (display {display})")
            
            try:
                # Build FFmpeg command
                cmd = [
                    "ffmpeg",
                    "-y",  # Overwrite output file
                    "-f", "x11grab",
                    "-video_size", f"{settings.screen_width}x{settings.screen_height}",
                    "-framerate", str(fps),
                    "-i", display,
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", str(crf),
                    "-pix_fmt", "yuv420p",
                    str(output_path),
                ]
                
                logger.debug(f"FFmpeg command: {' '.join(cmd)}")
                
                # Start FFmpeg process
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,  # Capture for debugging
                )
                
                # Create recording info
                recording = RecordingInfo(
                    session_id=session_id,
                    display_num=display_num,
                    output_path=output_path,
                    ffmpeg_pid=proc.pid,
                    started_at=time.time(),
                )
                
                # Track the recording
                self._recordings[session_id] = recording
                
                logger.info(
                    f"Recording started for session {session_id} "
                    f"(pid: {proc.pid}, output: {output_path})"
                )
                
                return recording
                
            except Exception as e:
                logger.error(f"Failed to start recording for session {session_id}: {e}")
                raise RuntimeError(f"Failed to start recording: {e}")
    
    async def stop_recording(self, session_id: str) -> Optional[Path]:
        """
        Stop recording and finalize the video file.
        
        Sends SIGINT to FFmpeg for graceful shutdown, which ensures
        the video file is properly finalized with correct metadata.
        
        Args:
            session_id: Session identifier (validated for security)
        
        Returns:
            Path to the video file, or None if no recording existed
        
        Raises:
            ValueError: If session_id is invalid
        """
        # Security: validate session_id
        self._validate_session_id(session_id)
        
        async with self._lock:
            if session_id not in self._recordings:
                logger.warning(f"No recording found for session {session_id}")
                return None
            
            recording = self._recordings[session_id]
            logger.info(
                f"Stopping recording for session {session_id} "
                f"(duration: {recording.duration_seconds:.1f}s)"
            )
            
            if recording.ffmpeg_pid:
                try:
                    # Send SIGINT for graceful shutdown
                    # This allows FFmpeg to finalize the video properly
                    os.kill(recording.ffmpeg_pid, signal.SIGINT)
                    
                    # Wait for process to finish
                    for _ in range(30):  # Max 3 seconds
                        try:
                            os.kill(recording.ffmpeg_pid, 0)
                            await asyncio.sleep(0.1)
                        except ProcessLookupError:
                            break
                    else:
                        # Force kill if still running
                        os.kill(recording.ffmpeg_pid, signal.SIGKILL)
                        
                except ProcessLookupError:
                    pass  # Already ended
                except Exception as e:
                    logger.warning(f"Error stopping FFmpeg: {e}")
            
            # Remove from tracking
            del self._recordings[session_id]
            
            # Verify output file exists
            if recording.output_path.exists():
                file_size = recording.output_path.stat().st_size
                logger.info(
                    f"Recording saved: {recording.output_path} "
                    f"({file_size / 1024 / 1024:.1f} MB)"
                )
                return recording.output_path
            else:
                logger.warning(f"Recording file not found: {recording.output_path}")
                return None
    
    def get_recording_info(self, session_id: str) -> Optional[RecordingInfo]:
        """Get recording information for a session."""
        self._validate_session_id(session_id)  # Security check
        return self._recordings.get(session_id)
    
    def get_recording_path(self, session_id: str) -> Optional[Path]:
        """
        Get the path to a session's recording with security validation.
        
        Returns the path if the recording file exists, even if
        the recording is no longer active.
        
        Args:
            session_id: Session identifier (validated for security)
        
        Returns:
            Path to recording file, or None if not found
        
        Raises:
            ValueError: If session_id is invalid (path traversal attempt)
        """
        # Security: validate and get safe path
        path = self._get_safe_recording_path(session_id)
        return path if path.exists() else None
    
    def is_recording(self, session_id: str) -> bool:
        """Check if a session is currently being recorded."""
        info = self._recordings.get(session_id)
        return info is not None and info.is_active
    
    @property
    def active_recording_count(self) -> int:
        """Get the number of active recordings."""
        return len(self._recordings)
    
    async def shutdown(self) -> None:
        """
        Stop all recordings gracefully.
        
        Should be called when the application is shutting down.
        """
        logger.info("Shutting down all recordings...")
        
        session_ids = list(self._recordings.keys())
        for session_id in session_ids:
            await self.stop_recording(session_id)
        
        logger.info("All recordings stopped")


# =============================================================================
# Global Instance
# =============================================================================

# Singleton recording manager for use across the application
recording_manager = RecordingManager()
```

### 4.3 Configuration Settings

Add to `app/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # ==========================================================================
    # Recording Settings
    # ==========================================================================
    
    # Enable/disable session recording
    recording_enabled: bool = Field(
        default=False, 
        env="RECORDING_ENABLED",
        description="Enable video recording of sessions"
    )
    
    # Recordings directory
    recordings_dir: str = Field(
        default="/sessions/recordings",
        env="RECORDINGS_DIR",
        description="Directory to store session recordings"
    )
    
    # Recording quality (frames per second)
    recording_fps: int = Field(
        default=15,
        env="RECORDING_FPS",
        description="Recording frame rate (10-30 recommended)"
    )
    
    # Recording quality (CRF: 0-51, lower = better quality, larger file)
    recording_crf: int = Field(
        default=28,
        env="RECORDING_CRF",
        description="Recording quality (18-28 recommended, lower = better)"
    )
    
    # Maximum recording duration (seconds, 0 = unlimited)
    recording_max_duration: int = Field(
        default=3600,
        env="RECORDING_MAX_DURATION",
        description="Maximum recording duration in seconds (0 = unlimited)"
    )
    
    # Auto-delete recordings after session cleanup
    recording_auto_delete: bool = Field(
        default=False,
        env="RECORDING_AUTO_DELETE",
        description="Delete recordings when sessions are cleaned up"
    )
```

### 4.4 Session Manager Integration

Modify `app/services/session_manager.py`:

```python
from .recording_manager import recording_manager

class SessionManager:
    
    async def create_session(self, ...):
        # ... existing code ...
        
        # Create display
        display_info = await display_manager.create_display(session.id)
        
        # Start recording (if enabled)
        if settings.recording_enabled:
            try:
                await recording_manager.start_recording(
                    session_id=session.id,
                    display_num=display_info.display_num,
                )
                logger.info(f"Recording started for session {session.id}")
            except Exception as e:
                # Don't fail session creation if recording fails
                logger.warning(f"Could not start recording: {e}")
        
        # ... rest of code ...
    
    async def delete_session(self, ...):
        # Stop recording (if active)
        if settings.recording_enabled:
            video_path = await recording_manager.stop_recording(session_id)
            if video_path:
                logger.info(f"Recording saved: {video_path}")
        
        # ... existing cleanup code ...
```

### 4.5 Dockerfile Changes

Add FFmpeg to `docker/Dockerfile`:

```dockerfile
# Install nginx, zstd, and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    zstd \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

Add recordings directory:

```dockerfile
# Create directory structure
RUN mkdir -p /sessions/base/home/user/.config \
    && mkdir -p /sessions/base/home/user/.local/share \
    && mkdir -p /sessions/recordings \        # ADD THIS
    && chmod 1777 /sessions/base/tmp \
    && chown -R computeruse:computeruse /sessions
```

---

## 5. API & MCP Tools

### 5.1 REST API Endpoints

#### Get Session Recording

```
GET /api/v1/sessions/{session_id}/recording
```

Returns the video file for download.

**Response:**
- `200 OK` - Video file (Content-Type: video/mp4)
- `404 Not Found` - Recording doesn't exist

**Example:**
```bash
curl -O http://localhost:8000/api/v1/sessions/sess_abc123/recording
# Downloads: sess_abc123.mp4
```

#### Get Recording Info

```
GET /api/v1/sessions/{session_id}/recording/info
```

Returns metadata about the recording.

**Response:**
```json
{
  "session_id": "sess_abc123",
  "exists": true,
  "is_recording": false,
  "file_size_bytes": 15728640,
  "file_size_mb": 15.0,
  "duration_seconds": 180.5,
  "created_at": "2025-12-10T10:30:00Z"
}
```

### 5.2 API Route Implementation

```python
# app/api/routes/sessions.py (additions)

from fastapi.responses import FileResponse
from app.services.recording_manager import recording_manager

@router.get("/sessions/{session_id}/recording")
async def get_session_recording(
    session_id: str,
    session: DBSession = Depends(get_session_or_404),
):
    """
    Download the video recording of a session.
    
    Returns the MP4 video file if recording exists.
    """
    video_path = recording_manager.get_recording_path(session_id)
    
    if not video_path or not video_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Recording not found for this session"
        )
    
    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=f"session_{session_id}.mp4",
    )


@router.get("/sessions/{session_id}/recording/info")
async def get_session_recording_info(
    session_id: str,
    session: DBSession = Depends(get_session_or_404),
):
    """
    Get metadata about a session's recording.
    """
    video_path = recording_manager.get_recording_path(session_id)
    recording_info = recording_manager.get_recording_info(session_id)
    
    if video_path and video_path.exists():
        stat = video_path.stat()
        return {
            "session_id": session_id,
            "exists": True,
            "is_recording": recording_info is not None and recording_info.is_active,
            "file_size_bytes": stat.st_size,
            "file_size_mb": round(stat.st_size / 1024 / 1024, 2),
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        }
    else:
        return {
            "session_id": session_id,
            "exists": False,
            "is_recording": recording_info is not None and recording_info.is_active,
            "file_size_bytes": 0,
            "file_size_mb": 0,
        }
```

### 5.3 MCP Tools

Add to `app/mcp/tools.py`:

```python
# =========================================================================
# Tool: get_recording
# =========================================================================

@mcp.tool()
async def get_recording_info(session_id: str) -> dict[str, Any]:
    """
    Get information about a session's video recording.
    
    Each session can optionally be recorded as an MP4 video.
    Use this to check if a recording exists and get download info.
    
    Args:
        session_id: The session to check recording for
    
    Returns:
        exists: Whether a recording file exists
        is_recording: Whether recording is currently active
        file_size_mb: Recording file size in megabytes
        download_url: URL to download the recording (if exists)
    """
    from app.services.recording_manager import recording_manager
    
    video_path = recording_manager.get_recording_path(session_id)
    recording_info = recording_manager.get_recording_info(session_id)
    
    if video_path and video_path.exists():
        stat = video_path.stat()
        host = settings.api_host or "localhost:8000"
        return {
            "exists": True,
            "is_recording": recording_info is not None and recording_info.is_active,
            "file_size_mb": round(stat.st_size / 1024 / 1024, 2),
            "download_url": f"http://{host}/api/v1/sessions/{session_id}/recording",
        }
    else:
        return {
            "exists": False,
            "is_recording": recording_info is not None and recording_info.is_active,
            "file_size_mb": 0,
            "download_url": None,
        }
```

---

## 6. Cloud Storage (Cloudflare R2)

### 6.1 Why Cloudflare R2?

Render.com containers have **ephemeral storage** - data is lost on redeploy. We need external storage for recordings. After evaluating options, **Cloudflare R2** is the recommended choice:

| Option | Persistence | Scalability | Cost | Best For |
|--------|-------------|-------------|------|----------|
| **Cloudflare R2** ✅ | ✅ Permanent | ✅ Unlimited | 💰 Lowest | Production |
| AWS S3 | ✅ Permanent | ✅ Unlimited | 💰💰 Medium | AWS ecosystem |
| Render Disk | ✅ Permanent | ❌ Single instance | 💰💰 Medium | Development |
| MinIO on Render | ✅ Permanent | ❌ Single instance | 💰💰💰 High | Self-hosted S3 |

### 6.2 R2 Advantages

| Feature | Benefit |
|---------|---------|
| **Zero Egress Fees** | User downloads = $0 transfer cost |
| **S3-Compatible API** | Use boto3, same code works with S3 |
| **Free Tier** | 10 GB storage + 10M reads/month forever |
| **Global CDN** | Fast downloads via Cloudflare network |
| **Simple Pricing** | $0.015/GB/month, no surprises |

### 6.3 Cost Estimates

| Usage Scenario | Storage | Downloads | Monthly Cost |
|----------------|---------|-----------|--------------|
| 100 sessions × 50MB | 5 GB | 500 downloads | **$0** (free tier) |
| 500 sessions × 50MB | 25 GB | 2,000 downloads | **~$0.38** |
| 2,000 sessions × 50MB | 100 GB | 10,000 downloads | **~$1.50** |
| 10,000 sessions × 50MB | 500 GB | 50,000 downloads | **~$7.50** |

Compare to AWS S3 (same 100 GB scenario): **~$11.30/month** (7x more expensive due to egress)

### 6.4 Architecture with R2

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Recording Flow                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Render.com Container                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  1. FFmpeg records to /tmp/recordings/sess_abc123.mp4 (temporary)   │   │
│  │                              │                                       │   │
│  │  2. Session ends             ▼                                       │   │
│  │     └── RecordingManager.stop_recording()                           │   │
│  │                              │                                       │   │
│  │  3. Upload to R2             ▼                                       │   │
│  │     └── RecordingStorage.upload_recording()                         │   │
│  │                              │                                       │   │
│  │  4. Delete local file        ▼                                       │   │
│  │     └── /tmp/recordings/sess_abc123.mp4 removed                     │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                 │                                           │
│                                 │ HTTPS upload                              │
│                                 ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Cloudflare R2 Bucket                            │   │
│  │                                                                      │   │
│  │  deskcloud-recordings/                                               │   │
│  │  └── recordings/                                                     │   │
│  │      └── 2025/12/10/                                                │   │
│  │          ├── sess_abc123.mp4                                        │   │
│  │          ├── sess_def456.mp4                                        │   │
│  │          └── sess_ghi789.mp4                                        │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                 │                                           │
│                                 │ Signed URL (1 hour expiry)               │
│                                 ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      User Download                                    │   │
│  │                                                                      │   │
│  │  • Downloads via Cloudflare CDN                                     │   │
│  │  • Zero egress fees                                                 │   │
│  │  • Global edge caching                                              │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.5 RecordingStorage Service

```python
# app/services/recording_storage.py
"""
Recording Storage Service
=========================

Uploads session recordings to Cloudflare R2 for permanent storage.
Uses S3-compatible API via boto3.

R2 Benefits:
- Zero egress fees (user downloads are free)
- S3-compatible API
- Global CDN via Cloudflare
- $0.015/GB/month storage
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class RecordingStorage:
    """
    Handles upload/download of recordings to Cloudflare R2.
    
    Uses S3-compatible API, so this also works with AWS S3,
    MinIO, or any S3-compatible storage.
    
    Usage:
        storage = RecordingStorage()
        
        # Upload after recording completes
        key = await storage.upload_recording("sess_abc123", Path("/tmp/rec.mp4"))
        
        # Get download URL for user
        url = storage.get_download_url("sess_abc123")
        
        # Cleanup old recordings
        await storage.delete_recording("sess_abc123")
    """
    
    _instance: Optional["RecordingStorage"] = None
    
    def __new__(cls) -> "RecordingStorage":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the R2 client."""
        if self._initialized:
            return
        
        # Only initialize if R2 is configured
        if not settings.r2_enabled:
            logger.warning("R2 storage not configured, recordings will be local only")
            self._client = None
            self._initialized = True
            return
        
        self._client = boto3.client(
            's3',
            endpoint_url=settings.r2_endpoint,
            aws_access_key_id=settings.r2_access_key,
            aws_secret_access_key=settings.r2_secret_key,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'},
            ),
        )
        self._bucket = settings.r2_bucket
        self._initialized = True
        
        logger.info(f"RecordingStorage initialized (bucket: {self._bucket})")
    
    @property
    def is_enabled(self) -> bool:
        """Check if R2 storage is enabled and configured."""
        return self._client is not None
    
    # =========================================================================
    # Upload
    # =========================================================================
    
    async def upload_recording(
        self,
        session_id: str,
        local_path: Path,
        delete_local: bool = True,
    ) -> Optional[str]:
        """
        Upload recording to R2 and return the object key.
        
        Organizes recordings by date for easier management and lifecycle rules.
        
        Args:
            session_id: Session identifier
            local_path: Path to local MP4 file
            delete_local: Whether to delete local file after upload
        
        Returns:
            Object key in R2 bucket, or None if upload failed
        """
        if not self.is_enabled:
            logger.warning("R2 not enabled, skipping upload")
            return None
        
        if not local_path.exists():
            logger.error(f"Local file not found: {local_path}")
            return None
        
        # Validate session_id (security)
        self._validate_session_id(session_id)
        
        # Organize by date for lifecycle management
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        object_key = f"recordings/{date_prefix}/{session_id}.mp4"
        
        try:
            file_size = local_path.stat().st_size
            logger.info(
                f"Uploading recording to R2: {object_key} "
                f"({file_size / 1024 / 1024:.1f} MB)"
            )
            
            self._client.upload_file(
                Filename=str(local_path),
                Bucket=self._bucket,
                Key=object_key,
                ExtraArgs={
                    'ContentType': 'video/mp4',
                    'Metadata': {
                        'session-id': session_id,
                        'uploaded-at': datetime.utcnow().isoformat(),
                    },
                },
            )
            
            logger.info(f"Upload complete: {object_key}")
            
            # Delete local file after successful upload
            if delete_local:
                local_path.unlink(missing_ok=True)
                logger.debug(f"Deleted local file: {local_path}")
            
            return object_key
            
        except ClientError as e:
            logger.error(f"R2 upload failed: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected upload error: {e}")
            return None
    
    # =========================================================================
    # Download URL
    # =========================================================================
    
    def get_download_url(
        self,
        session_id: str,
        expires_in: int = 3600,  # 1 hour
    ) -> Optional[str]:
        """
        Generate a signed URL for downloading a recording.
        
        The URL is pre-signed and expires after the specified time.
        Users download directly from Cloudflare's CDN (zero egress cost).
        
        Args:
            session_id: Session identifier
            expires_in: URL expiration in seconds (default 1 hour)
        
        Returns:
            Signed download URL, or None if not found
        """
        if not self.is_enabled:
            return None
        
        # Validate session_id (security)
        self._validate_session_id(session_id)
        
        # Find the recording
        object_key = self._find_recording(session_id)
        if not object_key:
            return None
        
        try:
            url = self._client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self._bucket,
                    'Key': object_key,
                },
                ExpiresIn=expires_in,
            )
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate download URL: {e}")
            return None
    
    # =========================================================================
    # Recording Info
    # =========================================================================
    
    def get_recording_info(self, session_id: str) -> Optional[dict]:
        """
        Get metadata about a recording in R2.
        
        Returns:
            Dict with size, uploaded_at, etc. or None if not found
        """
        if not self.is_enabled:
            return None
        
        self._validate_session_id(session_id)
        
        object_key = self._find_recording(session_id)
        if not object_key:
            return None
        
        try:
            response = self._client.head_object(
                Bucket=self._bucket,
                Key=object_key,
            )
            
            return {
                'exists': True,
                'object_key': object_key,
                'size_bytes': response['ContentLength'],
                'size_mb': round(response['ContentLength'] / 1024 / 1024, 2),
                'uploaded_at': response['LastModified'].isoformat(),
                'content_type': response['ContentType'],
            }
            
        except ClientError:
            return None
    
    def recording_exists(self, session_id: str) -> bool:
        """Check if a recording exists in R2."""
        return self.get_recording_info(session_id) is not None
    
    # =========================================================================
    # Delete
    # =========================================================================
    
    async def delete_recording(self, session_id: str) -> bool:
        """
        Delete a recording from R2.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if deleted, False if not found or failed
        """
        if not self.is_enabled:
            return False
        
        self._validate_session_id(session_id)
        
        object_key = self._find_recording(session_id)
        if not object_key:
            return False
        
        try:
            self._client.delete_object(
                Bucket=self._bucket,
                Key=object_key,
            )
            logger.info(f"Deleted recording from R2: {object_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete recording: {e}")
            return False
    
    # =========================================================================
    # Helpers
    # =========================================================================
    
    def _validate_session_id(self, session_id: str) -> None:
        """Validate session_id to prevent path traversal."""
        import re
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            raise ValueError(f"Invalid session_id format: {session_id}")
    
    def _find_recording(self, session_id: str) -> Optional[str]:
        """
        Find recording by session_id.
        
        Searches the bucket for a recording matching the session_id.
        """
        try:
            # List objects with prefix filter
            paginator = self._client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(
                Bucket=self._bucket,
                Prefix='recordings/',
            ):
                for obj in page.get('Contents', []):
                    if session_id in obj['Key']:
                        return obj['Key']
            
            return None
            
        except ClientError:
            return None


# =============================================================================
# Global Instance
# =============================================================================

recording_storage = RecordingStorage()
```

### 6.6 Integration with RecordingManager

Update `SessionManager` to upload after recording stops:

```python
# In session_manager.py

from .recording_storage import recording_storage

async def delete_session(self, ...):
    # Stop recording
    if settings.recording_enabled:
        video_path = await recording_manager.stop_recording(session_id)
        
        # Upload to R2
        if video_path and recording_storage.is_enabled:
            object_key = await recording_storage.upload_recording(
                session_id=session_id,
                local_path=video_path,
                delete_local=True,  # Remove local copy after upload
            )
            
            if object_key:
                logger.info(f"Recording uploaded to R2: {object_key}")
            else:
                logger.warning(f"Failed to upload recording for {session_id}")
    
    # ... rest of cleanup
```

### 6.7 Updated API Endpoint

```python
# In sessions.py routes

@router.get("/sessions/{session_id}/recording")
async def get_session_recording(
    session_id: str,
    session: DBSession = Depends(get_session_or_404),
):
    """
    Get download URL for session recording.
    
    Returns a signed URL that expires in 1 hour.
    User downloads directly from Cloudflare CDN (zero egress cost).
    """
    from app.services.recording_storage import recording_storage
    
    # Check R2 first
    if recording_storage.is_enabled:
        download_url = recording_storage.get_download_url(session_id)
        
        if download_url:
            return {
                "session_id": session_id,
                "download_url": download_url,
                "expires_in": 3600,
                "storage": "r2",
            }
    
    # Fallback to local storage (development)
    video_path = recording_manager.get_recording_path(session_id)
    if video_path:
        return FileResponse(
            path=video_path,
            media_type="video/mp4",
            filename=f"session_{session_id}.mp4",
        )
    
    raise HTTPException(404, "Recording not found")
```

---

## 7. Storage Lifecycle & Cleanup

### 7.1 Storage Structure

**Local (temporary during recording):**
```
/tmp/recordings/           # Temporary during session
└── sess_abc123.mp4        # Deleted after R2 upload
```

**R2 (permanent storage):**
```
deskcloud-recordings/      # R2 bucket
└── recordings/
    └── 2025/
        └── 12/
            └── 10/
                ├── sess_abc123.mp4
                ├── sess_def456.mp4
                └── sess_ghi789.mp4
```

### 7.2 Recording Size Estimates

| Session Duration | 15fps, CRF 28 | 10fps, CRF 32 | 5fps, CRF 35 |
|------------------|---------------|---------------|--------------|
| 5 minutes | ~25-50 MB | ~15-30 MB | ~5-15 MB |
| 15 minutes | ~75-150 MB | ~45-90 MB | ~15-45 MB |
| 30 minutes | ~150-300 MB | ~90-180 MB | ~30-90 MB |
| 1 hour | ~300-600 MB | ~180-360 MB | ~60-180 MB |

### 7.3 R2 Lifecycle Rules

Configure automatic cleanup in Cloudflare R2 dashboard:

```yaml
# Example lifecycle rule (set in R2 dashboard)
Rule: Delete recordings older than 30 days
  Prefix: recordings/
  Action: Delete after 30 days
```

### 7.4 Manual Cleanup

```python
# Cleanup recordings older than N days
async def cleanup_old_recordings(max_age_days: int = 30):
    """Delete recordings older than specified days from R2."""
    from datetime import datetime, timedelta
    
    if not recording_storage.is_enabled:
        return
    
    cutoff = datetime.utcnow() - timedelta(days=max_age_days)
    
    paginator = recording_storage._client.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(
        Bucket=recording_storage._bucket,
        Prefix='recordings/',
    ):
        for obj in page.get('Contents', []):
            if obj['LastModified'].replace(tzinfo=None) < cutoff:
                recording_storage._client.delete_object(
                    Bucket=recording_storage._bucket,
                    Key=obj['Key'],
                )
                logger.info(f"Deleted old recording: {obj['Key']}")
```

---

## 8. Configuration Options

### 8.1 Recording Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RECORDING_ENABLED` | `false` | Enable video recording |
| `RECORDINGS_DIR` | `/tmp/recordings` | Local temp directory |
| `RECORDING_FPS` | `15` | Frames per second |
| `RECORDING_CRF` | `28` | Quality (18-28) |
| `RECORDING_MAX_DURATION` | `3600` | Max duration (seconds) |

### 8.2 Cloudflare R2 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `R2_ENABLED` | `false` | Enable R2 cloud storage |
| `R2_ENDPOINT` | - | R2 endpoint URL |
| `R2_ACCESS_KEY` | - | R2 access key ID |
| `R2_SECRET_KEY` | - | R2 secret access key |
| `R2_BUCKET` | `deskcloud-recordings` | R2 bucket name |
| `R2_RETENTION_DAYS` | `30` | Auto-delete after N days |

### 8.3 Example Configuration

```bash
# .env or Render.com environment variables

# Enable recording
RECORDING_ENABLED=true
RECORDING_FPS=15
RECORDING_CRF=28

# Cloudflare R2 (required for production)
R2_ENABLED=true
R2_ENDPOINT=https://<account_id>.r2.cloudflarestorage.com
R2_ACCESS_KEY=<your_access_key_id>
R2_SECRET_KEY=<your_secret_access_key>
R2_BUCKET=deskcloud-recordings
R2_RETENTION_DAYS=30
```

### 8.4 Cloudflare R2 Setup

1. **Create Cloudflare Account** (free)
   - Go to https://dash.cloudflare.com/
   - Sign up or log in

2. **Enable R2**
   - Navigate to R2 in sidebar
   - Click "Create bucket"
   - Name: `deskcloud-recordings`

3. **Create API Token**
   - Go to R2 → Manage R2 API Tokens
   - Create token with:
     - Permission: Object Read & Write
     - Bucket: `deskcloud-recordings`
   - Copy Access Key ID and Secret Access Key

4. **Get Account ID**
   - Find in URL: `dash.cloudflare.com/<account_id>/r2`
   - Endpoint: `https://<account_id>.r2.cloudflarestorage.com`

5. **Configure Lifecycle Rule** (optional)
   - In R2 bucket settings
   - Add rule: Delete objects older than 30 days

### 8.5 Settings Class Addition

```python
# Add to app/config.py

class Settings(BaseSettings):
    # ... existing settings ...
    
    # ==========================================================================
    # Recording Settings
    # ==========================================================================
    
    recording_enabled: bool = Field(
        default=False,
        env="RECORDING_ENABLED",
    )
    
    recordings_dir: str = Field(
        default="/tmp/recordings",
        env="RECORDINGS_DIR",
    )
    
    recording_fps: int = Field(default=15, env="RECORDING_FPS")
    recording_crf: int = Field(default=28, env="RECORDING_CRF")
    recording_max_duration: int = Field(default=3600, env="RECORDING_MAX_DURATION")
    
    # ==========================================================================
    # Cloudflare R2 Settings
    # ==========================================================================
    
    r2_enabled: bool = Field(
        default=False,
        env="R2_ENABLED",
    )
    
    r2_endpoint: str = Field(
        default="",
        env="R2_ENDPOINT",
    )
    
    r2_access_key: str = Field(
        default="",
        env="R2_ACCESS_KEY",
    )
    
    r2_secret_key: str = Field(
        default="",
        env="R2_SECRET_KEY",
    )
    
    r2_bucket: str = Field(
        default="deskcloud-recordings",
        env="R2_BUCKET",
    )
    
    r2_retention_days: int = Field(
        default=30,
        env="R2_RETENTION_DAYS",
    )
```

### 8.6 Quality Presets

| Preset | FPS | CRF | Size/min | Use Case |
|--------|-----|-----|----------|----------|
| **High Quality** | 30 | 23 | ~15 MB | Demos, marketing |
| **Standard** | 15 | 28 | ~8 MB | Default, debugging |
| **Compressed** | 10 | 32 | ~4 MB | Long sessions |
| **Minimal** | 5 | 35 | ~2 MB | Audit trail only |

---

## 9. Resource Impact

### 9.1 Per-Session Overhead

| Resource | Without Recording | With Recording | Delta |
|----------|-------------------|----------------|-------|
| RAM | ~100 MB | ~130-150 MB | +30-50 MB |
| CPU | ~5% | ~10-15% | +5-10% |
| Disk I/O | Low | Moderate | Continuous writes |
| Storage | 0 | ~5-10 MB/min | Linear growth |

### 9.2 Scalability Considerations

With 20 concurrent sessions:
- Additional RAM: ~600 MB - 1 GB
- Additional CPU: ~100-200% (2 cores equivalent)
- Disk writes: ~100-200 MB/min total

**Recommendation:** Use SSD for local temp storage, R2 for permanent storage.

### 9.3 Optimization Tips

1. **Lower FPS for long sessions**: 10fps is sufficient for most use cases
2. **Increase CRF for smaller files**: CRF 32 is still watchable
3. **R2 for permanent storage**: Zero egress fees, global CDN
4. **Lifecycle rules**: Auto-delete old recordings in R2

---

## 10. Security Considerations

### 10.1 Session Isolation (Critical)

**A session MUST NOT be able to access recordings from other sessions.**

This is enforced at multiple levels:

#### Level 1: Storage Isolation (Local + Cloud)

Recordings are stored in two places, **neither accessible from within the session**:

**Local (temporary, during recording):**
```
/tmp/recordings/              # OUTSIDE session namespace
└── sess_abc123.mp4           # Temporary, deleted after R2 upload
```

**Cloud (permanent, Cloudflare R2):**
```
deskcloud-recordings/         # R2 bucket (cloud storage)
└── recordings/
    └── 2025/12/10/
        ├── sess_abc123.mp4   # Permanent storage
        └── sess_def456.mp4   # Accessible only via signed URLs
```

**Session filesystem (isolated):**
```
/sessions/active/
└── sess_abc123/              # Session's isolated filesystem
    └── merged/               # What the session sees as "/"
        └── home/user/        # Session can only access this
```

The session process runs with:
- `HOME=/sessions/active/{session_id}/merged/home/user`
- **No access to `/tmp/recordings/`** (outside OverlayFS)
- **No access to R2** (cloud storage, requires API credentials)

#### Level 2: Process Namespace Isolation

Each session's processes run in an isolated environment:

```python
# Environment set for session processes
session_env = {
    "HOME": f"/sessions/active/{session_id}/merged/home/user",
    "TMPDIR": f"/sessions/active/{session_id}/merged/tmp",
    # Recordings directory is NOT exposed
}
```

#### Level 3: API Access Control

All recording access goes through authenticated API endpoints:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Recording Access Flow                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Session A (Agent)                    Session B (Agent)              │
│       │                                    │                         │
│       ├── Cannot access filesystem ────────┤                         │
│       │   /sessions/recordings/            │                         │
│       │                                    │                         │
│       ▼                                    ▼                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Backend                           │   │
│  │                                                              │   │
│  │  GET /sessions/{id}/recording                                │   │
│  │       │                                                      │   │
│  │       ├── Validate session_id format                        │   │
│  │       ├── Verify session exists in database                 │   │
│  │       ├── Check user ownership (if auth enabled)            │   │
│  │       └── Return recording ONLY for requested session       │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 10.2 Path Traversal Prevention

The `RecordingManager` validates session IDs to prevent path traversal attacks:

```python
# In RecordingManager

def _validate_session_id(self, session_id: str) -> bool:
    """
    Validate session_id to prevent path traversal.
    
    Valid: sess_abc123, session_def456
    Invalid: ../etc/passwd, sess_abc/../other, /etc/passwd
    """
    import re
    
    # Only allow alphanumeric, underscore, hyphen
    if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
        raise ValueError(f"Invalid session_id format: {session_id}")
    
    # Ensure no path components
    if '/' in session_id or '\\' in session_id or '..' in session_id:
        raise ValueError(f"Invalid session_id: path traversal detected")
    
    return True

def get_recording_path(self, session_id: str) -> Optional[Path]:
    """Get recording path with validation."""
    self._validate_session_id(session_id)
    
    path = self._recordings_dir / f"{session_id}.mp4"
    
    # Ensure path is within recordings directory (defense in depth)
    try:
        path.resolve().relative_to(self._recordings_dir.resolve())
    except ValueError:
        raise ValueError(f"Path escape attempt detected: {session_id}")
    
    return path if path.exists() else None
```

### 10.3 MCP Tool Isolation

MCP tools can only access recordings for sessions created in the same MCP context:

```python
# In app/mcp/tools.py

@mcp.tool()
async def get_recording_info(session_id: str) -> dict[str, Any]:
    """Get recording info - only for sessions in current context."""
    
    # Get MCP context (tracks sessions created in this connection)
    ctx = get_mcp_context()
    
    # CRITICAL: Verify session belongs to this MCP context
    if session_id not in ctx.session_ids:
        return {
            "error": f"Session {session_id} not found in current context",
            "exists": False,
        }
    
    # Proceed with recording info retrieval
    # ...
```

This ensures:
- An MCP client can only access recordings for sessions it created
- Even with a valid session_id, other MCP clients cannot access it
- The LLM cannot be tricked into accessing other sessions

### 10.4 Access Control Matrix

| Actor | Own Session Recording | Other Session Recording | R2 Direct Access |
|-------|----------------------|-------------------------|------------------|
| **Session Process** | ❌ No access | ❌ No access | ❌ No credentials |
| **REST API (no auth)** | ✅ Signed URL | ❌ Needs session_id | ❌ No credentials |
| **REST API (with auth)** | ✅ If owner | ❌ 403 Forbidden | ❌ No credentials |
| **MCP Tool** | ✅ If in context | ❌ Context check fails | ❌ No credentials |
| **Backend Service** | ✅ Upload/URL gen | ✅ Upload/URL gen | ✅ Has credentials |
| **Admin (R2 console)** | ✅ Full access | ✅ Full access | ✅ Cloudflare login |

### 10.5 Implementation Checklist

```
□ Local recordings in /tmp/recordings/ (outside OverlayFS)
□ Session processes have no access to temp recordings
□ R2 credentials only in backend environment variables
□ Session_id validation with regex (alphanumeric only)
□ Path traversal prevention in object keys
□ MCP context tracking for session ownership
□ Signed URLs expire after 1 hour
□ No session_id enumeration (can't list other recordings)
□ Audit logging for recording access attempts
□ R2 lifecycle rules for automatic deletion
```

### 10.6 Data Protection

| Concern | Mitigation |
|---------|------------|
| Sensitive data in recordings | Recordings follow same session permissions |
| Unauthorized access | Multi-layer isolation (local + R2 + API + context) |
| Session enumeration | Session IDs are UUIDs, no listing of other sessions |
| Path/key traversal | Strict validation + key prefix checks |
| Data retention | R2 lifecycle rules (auto-delete after 30 days) |
| Storage encryption | R2 encrypts data at rest |
| Signed URL expiry | URLs expire after 1 hour |
| R2 credential exposure | Credentials only in backend env vars |

### 10.7 API Access Control Implementation

```python
# Full implementation with all security checks

@router.get("/sessions/{session_id}/recording")
async def get_recording(
    session_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    repo: SessionRepository = Depends(get_session_repo),
):
    """
    Download session recording with security checks.
    """
    # 1. Validate session_id format (prevent path traversal)
    if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
        raise HTTPException(400, "Invalid session ID format")
    
    # 2. Verify session exists
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    # 3. Check ownership (if authentication is enabled)
    if current_user and session.user_id:
        if session.user_id != current_user.id:
            # Log access attempt
            logger.warning(
                f"Unauthorized recording access attempt: "
                f"user={current_user.id} session={session_id}"
            )
            raise HTTPException(403, "Not authorized to access this recording")
    
    # 4. Get recording path (with path validation)
    video_path = recording_manager.get_recording_path(session_id)
    if not video_path:
        raise HTTPException(404, "Recording not found")
    
    # 5. Return file
    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=f"session_{session_id}.mp4",
    )
```

### 10.8 Privacy Considerations

- Recordings may capture passwords typed in browser
- Financial data may be visible on screen
- Personal information may appear in recordings
- Consider warning users that sessions are recorded
- Implement data retention policies for compliance

---

## 11. Dashboard & Frontend Integration

This section describes how video recording integrates with the Next.js dashboard (see [nextjs_landing_dashboard.md](./nextjs_landing_dashboard.md)).

### 11.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Recording in Dashboard Flow                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Next.js Dashboard (Vercel)                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  Sessions List Page                    Session Detail Page           │   │
│  │  ┌───────────────────────┐            ┌───────────────────────┐    │   │
│  │  │ Session Card          │            │ VNC Viewer            │    │   │
│  │  │ ├── Title             │            │ (live view)           │    │   │
│  │  │ ├── Status            │            ├───────────────────────┤    │   │
│  │  │ ├── 🔴 Recording      │  ◀─────▶  │ Recording Player      │    │   │
│  │  │ └── Duration          │            │ (after session ends)  │    │   │
│  │  └───────────────────────┘            │ ├── Play/Pause        │    │   │
│  │                                        │ ├── Seek              │    │   │
│  │                                        │ ├── Download          │    │   │
│  │                                        │ └── Fullscreen        │    │   │
│  │                                        └───────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      │ API Calls                            │
│                                      ▼                                      │
│  FastAPI Backend (Render.com)                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                      │   │
│  │  GET /sessions/{id}                  GET /sessions/{id}/recording   │   │
│  │       │                                    │                         │   │
│  │       ▼                                    ▼                         │   │
│  │  Returns session with                Returns signed R2 URL          │   │
│  │  recording_status field              for direct CDN download         │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      │ Signed URL                          │
│                                      ▼                                      │
│  Cloudflare R2 → CDN → User Browser (video playback)                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Session Response Extension

Extend the session API response to include recording info:

```typescript
// src/types/session.ts (Next.js)

interface Session {
  id: string
  title: string | null
  status: 'active' | 'processing' | 'completed' | 'error' | 'archived'
  model: string
  provider: string
  display_num: number | null
  vnc_port: number | null
  novnc_port: number | null
  created_at: string
  updated_at: string
  last_activity: string
  
  // NEW: Recording fields
  recording: {
    status: 'recording' | 'processing' | 'available' | 'failed' | 'none'
    is_recording: boolean
    duration_seconds: number | null
    file_size_mb: number | null
    download_url: string | null  // Signed URL (null if not available)
    expires_at: string | null    // When download URL expires
  } | null
}
```

Backend response example:

```json
{
  "id": "sess_abc123",
  "title": "Web Scraping Task",
  "status": "completed",
  "recording": {
    "status": "available",
    "is_recording": false,
    "duration_seconds": 245,
    "file_size_mb": 18.5,
    "download_url": "https://deskcloud-recordings.r2.cloudflarestorage.com/...",
    "expires_at": "2025-12-10T15:30:00Z"
  }
}
```

### 11.3 Session Card Component

Update the session card to show recording status:

```tsx
// src/components/dashboard/session-card.tsx

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { 
  Monitor, 
  Circle, 
  Video, 
  Download, 
  Play,
  Loader2 
} from "lucide-react"
import Link from "next/link"
import type { Session } from "@/types/session"

interface SessionCardProps {
  session: Session
}

export function SessionCard({ session }: SessionCardProps) {
  const recordingStatus = session.recording?.status

  return (
    <Card className="hover:border-primary/50 transition-colors">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <Monitor className="h-4 w-4 text-muted-foreground" />
          <CardTitle className="text-sm font-medium">
            {session.title || `Session ${session.id.slice(-8)}`}
          </CardTitle>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Recording Status Badge */}
          {recordingStatus === 'recording' && (
            <Badge variant="destructive" className="gap-1">
              <Circle className="h-2 w-2 fill-current animate-pulse" />
              Recording
            </Badge>
          )}
          {recordingStatus === 'processing' && (
            <Badge variant="secondary" className="gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              Processing
            </Badge>
          )}
          {recordingStatus === 'available' && (
            <Badge variant="outline" className="gap-1 text-green-600 border-green-600">
              <Video className="h-3 w-3" />
              Recording
            </Badge>
          )}
          
          {/* Session Status Badge */}
          <Badge 
            variant={session.status === 'active' ? 'default' : 'secondary'}
          >
            {session.status}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>{session.model}</span>
          <span>{formatDuration(session.recording?.duration_seconds)}</span>
        </div>
        
        <div className="mt-4 flex gap-2">
          <Button asChild variant="outline" size="sm" className="flex-1">
            <Link href={`/dashboard/sessions/${session.id}`}>
              View Details
            </Link>
          </Button>
          
          {recordingStatus === 'available' && session.recording?.download_url && (
            <Button 
              variant="outline" 
              size="sm"
              asChild
            >
              <a 
                href={session.recording.download_url} 
                download={`session_${session.id}.mp4`}
              >
                <Download className="h-4 w-4" />
              </a>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
```

### 11.4 Recording Player Component

New component for viewing recordings:

```tsx
// src/components/dashboard/recording-player.tsx

"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Badge } from "@/components/ui/badge"
import {
  Play,
  Pause,
  Maximize2,
  Minimize2,
  Download,
  Volume2,
  VolumeX,
  RotateCcw,
  Loader2,
} from "lucide-react"
import type { Session } from "@/types/session"

interface RecordingPlayerProps {
  session: Session
  onRefreshUrl?: () => Promise<string>  // Refresh signed URL if expired
}

export function RecordingPlayer({ session, onRefreshUrl }: RecordingPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(true)  // Videos have no audio, but just in case
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [videoUrl, setVideoUrl] = useState(session.recording?.download_url)

  const recording = session.recording
  
  if (!recording || recording.status !== 'available') {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Session Recording</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            {recording?.status === 'recording' && (
              <>
                <Loader2 className="h-8 w-8 animate-spin mb-2" />
                <p>Recording in progress...</p>
              </>
            )}
            {recording?.status === 'processing' && (
              <>
                <Loader2 className="h-8 w-8 animate-spin mb-2" />
                <p>Processing recording...</p>
              </>
            )}
            {recording?.status === 'failed' && (
              <p className="text-destructive">Recording failed</p>
            )}
            {(!recording || recording.status === 'none') && (
              <p>No recording available for this session</p>
            )}
          </div>
        </CardContent>
      </Card>
    )
  }

  // Check if URL is expired and refresh if needed
  useEffect(() => {
    if (recording.expires_at) {
      const expiresAt = new Date(recording.expires_at)
      const now = new Date()
      
      if (now >= expiresAt && onRefreshUrl) {
        onRefreshUrl().then(setVideoUrl).catch(console.error)
      }
    }
  }, [recording.expires_at, onRefreshUrl])

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const toggleFullscreen = () => {
    if (containerRef.current) {
      if (!document.fullscreenElement) {
        containerRef.current.requestFullscreen()
        setIsFullscreen(true)
      } else {
        document.exitFullscreen()
        setIsFullscreen(false)
      }
    }
  }

  const handleSeek = (value: number[]) => {
    if (videoRef.current) {
      videoRef.current.currentTime = value[0]
      setCurrentTime(value[0])
    }
  }

  const restart = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = 0
      videoRef.current.play()
      setIsPlaying(true)
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <Card ref={containerRef}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <CardTitle className="text-sm font-medium">Session Recording</CardTitle>
          <Badge variant="outline" className="text-xs">
            {recording.file_size_mb?.toFixed(1)} MB
          </Badge>
        </div>
        <Button 
          variant="outline" 
          size="sm"
          asChild
        >
          <a href={videoUrl || '#'} download={`session_${session.id}.mp4`}>
            <Download className="h-4 w-4 mr-2" />
            Download
          </a>
        </Button>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Video Player */}
        <div className="relative aspect-video overflow-hidden rounded-lg border bg-black">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/50">
              <Loader2 className="h-8 w-8 animate-spin text-white" />
            </div>
          )}
          
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/80">
              <div className="text-center text-white">
                <p className="text-sm text-red-400">{error}</p>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="mt-2"
                  onClick={() => {
                    setError(null)
                    setIsLoading(true)
                    if (videoRef.current) videoRef.current.load()
                  }}
                >
                  Retry
                </Button>
              </div>
            </div>
          )}
          
          <video
            ref={videoRef}
            src={videoUrl || undefined}
            className="h-full w-full"
            muted={isMuted}
            onLoadedMetadata={(e) => {
              setDuration(e.currentTarget.duration)
              setIsLoading(false)
            }}
            onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
            onEnded={() => setIsPlaying(false)}
            onError={() => setError('Failed to load video')}
            onClick={togglePlay}
          />
          
          {/* Play overlay */}
          {!isPlaying && !isLoading && !error && (
            <button
              onClick={togglePlay}
              className="absolute inset-0 flex items-center justify-center bg-black/30 hover:bg-black/40 transition-colors"
            >
              <div className="rounded-full bg-white/90 p-4">
                <Play className="h-8 w-8 text-black" fill="black" />
              </div>
            </button>
          )}
        </div>

        {/* Controls */}
        <div className="space-y-2">
          {/* Progress bar */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground w-10">
              {formatTime(currentTime)}
            </span>
            <Slider
              value={[currentTime]}
              max={duration}
              step={0.1}
              onValueChange={handleSeek}
              className="flex-1"
            />
            <span className="text-xs text-muted-foreground w-10 text-right">
              {formatTime(duration)}
            </span>
          </div>

          {/* Control buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="icon" onClick={togglePlay}>
                {isPlaying ? (
                  <Pause className="h-4 w-4" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
              </Button>
              <Button variant="ghost" size="icon" onClick={restart}>
                <RotateCcw className="h-4 w-4" />
              </Button>
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => setIsMuted(!isMuted)}
              >
                {isMuted ? (
                  <VolumeX className="h-4 w-4" />
                ) : (
                  <Volume2 className="h-4 w-4" />
                )}
              </Button>
            </div>
            
            <Button variant="ghost" size="icon" onClick={toggleFullscreen}>
              {isFullscreen ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
```

### 11.5 Session Detail Page Update

Update the session detail page to include the recording player:

```tsx
// src/app/(dashboard)/dashboard/sessions/[id]/page.tsx

import { Suspense } from "react"
import { notFound } from "next/navigation"
import { api } from "@/lib/api"
import { VNCViewer } from "@/components/dashboard/vnc-viewer"
import { RecordingPlayer } from "@/components/dashboard/recording-player"
import { SessionInfo } from "@/components/dashboard/session-info"
import { MessageHistory } from "@/components/dashboard/message-history"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

interface SessionDetailPageProps {
  params: { id: string }
}

export default async function SessionDetailPage({ params }: SessionDetailPageProps) {
  const session = await api.getSession(params.id).catch(() => null)
  
  if (!session) {
    notFound()
  }

  const isActive = session.status === 'active'
  const hasRecording = session.recording?.status === 'available'
  const isRecording = session.recording?.status === 'recording'

  return (
    <div className="container py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">
          {session.title || `Session ${session.id.slice(-8)}`}
        </h1>
        <SessionInfo session={session} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main content - 2 columns */}
        <div className="lg:col-span-2 space-y-6">
          {/* Tabs for Live View vs Recording */}
          <Tabs defaultValue={isActive ? "live" : "recording"}>
            <TabsList>
              <TabsTrigger value="live" disabled={!isActive}>
                Live View {isActive && "●"}
              </TabsTrigger>
              <TabsTrigger 
                value="recording" 
                disabled={!hasRecording && !isRecording}
              >
                Recording {isRecording && "🔴"}
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="live" className="mt-4">
              {isActive && session.novnc_port ? (
                <VNCViewer 
                  sessionId={session.id}
                  vncUrl={`https://api.deskcloud.app/vnc/${session.id}`}
                />
              ) : (
                <div className="rounded-lg border bg-muted p-8 text-center text-muted-foreground">
                  Session is not active. Live view unavailable.
                </div>
              )}
            </TabsContent>
            
            <TabsContent value="recording" className="mt-4">
              <RecordingPlayer 
                session={session}
                onRefreshUrl={async () => {
                  // Refresh the signed URL from the API
                  const data = await api.getSessionRecordingUrl(session.id)
                  return data.download_url
                }}
              />
            </TabsContent>
          </Tabs>
        </div>

        {/* Sidebar - 1 column */}
        <div className="space-y-6">
          <Suspense fallback={<div>Loading messages...</div>}>
            <MessageHistory sessionId={session.id} />
          </Suspense>
        </div>
      </div>
    </div>
  )
}
```

### 11.6 API Client Extension

Add recording-related methods to the API client:

```typescript
// src/lib/api.ts (additions)

class APIClient {
  // ... existing methods ...

  /**
   * Get recording info for a session
   */
  async getSessionRecordingInfo(sessionId: string) {
    return this.request<{
      session_id: string
      exists: boolean
      status: 'recording' | 'processing' | 'available' | 'failed' | 'none'
      file_size_mb: number | null
      duration_seconds: number | null
    }>(`/api/v1/sessions/${sessionId}/recording/info`)
  }

  /**
   * Get download URL for a session recording
   * Returns a signed URL that expires in 1 hour
   */
  async getSessionRecordingUrl(sessionId: string) {
    return this.request<{
      session_id: string
      download_url: string
      expires_in: number
      expires_at: string
      storage: 'r2' | 'local'
    }>(`/api/v1/sessions/${sessionId}/recording`)
  }
}
```

### 11.7 Landing Page Feature Addition

Add recording to the features list:

```typescript
// src/lib/features.ts (addition)

export const features = [
  // ... existing features ...
  
  {
    icon: Video,
    title: "Session Recording",
    description: "Every session is automatically recorded. Replay, debug, and share session videos. Stored securely in the cloud.",
  },
]
```

### 11.8 Pricing Tier Differentiation

Recording can be a differentiating feature across pricing tiers:

```typescript
// src/lib/pricing.ts (updated)

export const pricingTiers = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    features: [
      "100 sessions/month",
      "BYOK (your API key)",
      "Community support",
      "1 concurrent session",
      "Recordings kept 7 days",  // NEW
    ],
    // ...
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    features: [
      "1,000 sessions/month",
      "BYOK (your API key)",
      "Priority email support",
      "5 concurrent sessions",
      "Session analytics",
      "API access",
      "Recordings kept 30 days",  // NEW
      "Higher quality recordings",  // NEW
    ],
    highlighted: true,
    // ...
  },
  {
    name: "Team",
    price: "$99",
    period: "/month",
    features: [
      "5,000 sessions/month",
      "BYOK (your API key)",
      "Priority support",
      "20 concurrent sessions",
      "Team management",
      "Advanced analytics",
      "Shared API keys",
      "Recordings kept 90 days",  // NEW
      "Recording annotations",    // NEW (future)
    ],
    // ...
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    features: [
      "Unlimited sessions",
      "BYOK or managed keys",
      "Dedicated support",
      "Unlimited concurrency",
      "SSO/SAML",
      "SLA guarantee",
      "Custom integrations",
      "On-premise option",
      "Unlimited recording retention",  // NEW
      "Custom storage integration",     // NEW
    ],
    // ...
  },
]
```

### 11.9 User Settings for Recording

Add recording preferences to user settings:

```tsx
// src/app/(dashboard)/dashboard/settings/recording/page.tsx

"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { useToast } from "@/components/ui/use-toast"

export default function RecordingSettingsPage() {
  const { toast } = useToast()
  const [settings, setSettings] = useState({
    autoRecord: true,
    quality: 'standard',
    retentionDays: 30,
  })

  const handleSave = async () => {
    // Save to API
    toast({ title: "Settings saved" })
  }

  return (
    <div className="container max-w-2xl py-8">
      <h1 className="text-3xl font-bold mb-8">Recording Settings</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Session Recording</CardTitle>
          <CardDescription>
            Configure how your sessions are recorded
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Auto-record toggle */}
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="auto-record">Automatic Recording</Label>
              <p className="text-sm text-muted-foreground">
                Record all sessions automatically
              </p>
            </div>
            <Switch
              id="auto-record"
              checked={settings.autoRecord}
              onCheckedChange={(checked) => 
                setSettings(s => ({ ...s, autoRecord: checked }))
              }
            />
          </div>

          {/* Quality selection */}
          <div className="space-y-2">
            <Label>Recording Quality</Label>
            <Select 
              value={settings.quality}
              onValueChange={(value) => 
                setSettings(s => ({ ...s, quality: value }))
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="minimal">
                  Minimal (5 fps, ~2 MB/min)
                </SelectItem>
                <SelectItem value="standard">
                  Standard (15 fps, ~8 MB/min)
                </SelectItem>
                <SelectItem value="high">
                  High Quality (30 fps, ~15 MB/min)
                </SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">
              Higher quality uses more storage
            </p>
          </div>

          {/* Retention info */}
          <div className="rounded-lg border bg-muted/50 p-4">
            <p className="text-sm">
              <strong>Retention:</strong> Your recordings are kept for{" "}
              <strong>{settings.retentionDays} days</strong> based on your{" "}
              <a href="/dashboard/settings/billing" className="text-primary hover:underline">
                Pro plan
              </a>.
            </p>
          </div>

          <Button onClick={handleSave}>Save Settings</Button>
        </CardContent>
      </Card>
    </div>
  )
}
```

### 11.10 Dashboard Sidebar Update

Add Recording link to sidebar:

```tsx
// In src/components/dashboard/sidebar.tsx

const menuItems = [
  { title: "Overview", url: "/dashboard", icon: LayoutDashboard },
  { title: "Sessions", url: "/dashboard/sessions", icon: Monitor },
  { title: "Recordings", url: "/dashboard/recordings", icon: Video },  // NEW
  { title: "API Keys", url: "/dashboard/api-keys", icon: Key },
  { title: "Settings", url: "/dashboard/settings", icon: Settings },
]
```

### 11.11 Recordings List Page (Optional)

Dedicated page to browse all recordings:

```tsx
// src/app/(dashboard)/dashboard/recordings/page.tsx

import { Suspense } from "react"
import { api } from "@/lib/api"
import { RecordingGrid } from "@/components/dashboard/recording-grid"
import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"

export default function RecordingsPage() {
  return (
    <div className="container py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Recordings</h1>
        <p className="text-muted-foreground">
          Browse and download your session recordings
        </p>
      </div>

      {/* Search/Filter */}
      <div className="mb-6 flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input 
            placeholder="Search recordings..." 
            className="pl-9"
          />
        </div>
      </div>

      <Suspense fallback={<RecordingGridSkeleton />}>
        <RecordingGrid />
      </Suspense>
    </div>
  )
}
```

---

## 12. Future Enhancements

### 12.1 Live Streaming

Stream session activity in real-time via HLS:

```bash
ffmpeg -f x11grab -i :1 \
  -c:v libx264 -preset ultrafast \
  -f hls -hls_time 2 -hls_list_size 5 \
  /live/sess_abc123/playlist.m3u8
```

### 12.2 On-Demand Recording

Start/stop recording via API:

```
POST /api/v1/sessions/{id}/recording/start
POST /api/v1/sessions/{id}/recording/stop
```

### 12.3 Recording Annotations

Mark timestamps in recordings:

```json
{
  "markers": [
    {"time": 0, "label": "Session started"},
    {"time": 45, "label": "Opened Firefox"},
    {"time": 120, "label": "Completed task"}
  ]
}
```

### 12.4 Thumbnail Generation

Generate preview thumbnails and upload to R2:

```bash
ffmpeg -i recording.mp4 -ss 00:00:05 -vframes 1 thumbnail.jpg
# Upload to R2: recordings/{date}/{session_id}_thumb.jpg
```

### 12.5 Video Compression

Post-process recordings for smaller files before upload:

```bash
# Re-encode with slower preset for better compression
ffmpeg -i raw.mp4 -c:v libx264 -preset slow -crf 23 compressed.mp4
```

### 12.6 R2 Multipart Upload

For large recordings (>100MB), use multipart upload:

```python
# boto3 automatically uses multipart for large files
# Configure multipart threshold if needed
from boto3.s3.transfer import TransferConfig

config = TransferConfig(
    multipart_threshold=100 * 1024 * 1024,  # 100MB
    max_concurrency=10,
)
```

---

## 13. Implementation Plan

### Phase 1: Core Recording (Week 1)

- [ ] Add FFmpeg to Dockerfile
- [ ] Add boto3 to requirements.txt
- [ ] Create `RecordingManager` service
- [ ] Add recording configuration settings
- [ ] Integrate with `SessionManager` lifecycle
- [ ] Basic local recording testing

### Phase 2: Cloudflare R2 Integration (Week 1)

- [ ] Create Cloudflare R2 bucket
- [ ] Generate R2 API credentials
- [ ] Create `RecordingStorage` service
- [ ] Add R2 configuration settings
- [ ] Implement upload after recording stops
- [ ] Test R2 upload flow

### Phase 3: API & Access (Week 1-2)

- [ ] Add REST endpoint for recording download URL
- [ ] Add recording info endpoint
- [ ] Add MCP tool for recording info
- [ ] Update API documentation
- [ ] Update `llms.txt`

### Phase 4: Lifecycle & Cleanup (Week 2)

- [ ] Configure R2 lifecycle rules (30-day retention)
- [ ] Implement manual cleanup function
- [ ] Add recording metadata to session response
- [ ] Storage monitoring/alerts

### Phase 5: Frontend Integration (Week 2-3)

- [ ] Extend session API response with recording info
- [ ] Create `RecordingPlayer` component
- [ ] Update session card with recording status
- [ ] Update session detail page with tabs (Live/Recording)
- [ ] Add recording quality settings to user preferences
- [ ] Add "Recordings" page to dashboard
- [ ] Update landing page features section
- [ ] Update pricing tiers with recording retention info

### Phase 6: Polish & Testing (Week 3)

- [ ] Performance testing under load
- [ ] R2 upload reliability testing
- [ ] Large file handling (multipart)
- [ ] Video player testing across browsers
- [ ] URL expiration/refresh testing
- [ ] Documentation updates
- [ ] README updates

---

## 14. References

### FFmpeg Documentation
- [x11grab capture device](https://ffmpeg.org/ffmpeg-devices.html#x11grab)
- [H.264 encoding guide](https://trac.ffmpeg.org/wiki/Encode/H.264)
- [CRF guide](https://slhck.info/video/2017/02/24/crf-guide.html)

### Cloudflare R2 Documentation
- [R2 Documentation](https://developers.cloudflare.com/r2/)
- [R2 S3 API Compatibility](https://developers.cloudflare.com/r2/api/s3/)
- [R2 Pricing](https://developers.cloudflare.com/r2/pricing/)
- [R2 Presigned URLs](https://developers.cloudflare.com/r2/api/s3/presigned-urls/)

### Related Plans
- [Multi-Session Scaling](./multi_session_scaling.md) - Display architecture
- [Session Filesystem Isolation](./session_filesystem_isolation.md) - Storage structure
- [Session Snapshots](./session_snapshots.md) - CRIU integration
- [Next.js Landing & Dashboard](./nextjs_landing_dashboard.md) - Frontend integration
- [Custom Image Builder](./custom_image_builder.md) - Premium feature (Team/Enterprise tier)
- [Remote Agent Client](./remote_agent_client.md) - Record sessions on user's own computers
- [Multi-OS Support](./multi_os_support.md) - Recording works across all OS platforms

### External Resources
- [Xvfb + FFmpeg recording](https://stackoverflow.com/questions/16139591/recording-xvfb-video)
- [Docker video recording](https://github.com/SeleniumHQ/docker-selenium#video-recording)
- [boto3 S3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
