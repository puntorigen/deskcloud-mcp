# Session Filesystem Isolation: OverlayFS-Based Approach

> ⚠️ **Context**: See [`MASTER_ROADMAP.md`](./MASTER_ROADMAP.md) for project overview.

**Author:** Pablo Schaffner  
**Date:** December 2025  
**Status:** ✅ Implemented (Core Feature)  
**Category:** Open Source Core  
**Depends on:** [Multi-Session Scaling](./multi_session_scaling.md), [Session Snapshots](./session_snapshots.md)

---

## Executive Summary

### The Problem

With Multi-Display architecture, each session has **isolated visual state** (separate X11 displays), but they all share the **same filesystem**. This means:

- Session A can see files created by Session B
- Downloaded files leak between sessions
- Browser profiles/cookies may conflict
- No privacy between concurrent users

### The Solution

Use **OverlayFS (Copy-on-Write)** to give each session its own filesystem view:

1. **Base Layer** - Shared read-only (OS, apps, Firefox) ~500MB
2. **Upper Layer** - Per-session writable layer (starts at 0, grows as needed)
3. **Merged View** - Each session sees a "complete" filesystem

```
Session 1 View:                    Session 2 View:
┌────────────────────┐            ┌────────────────────┐
│ /home/user/        │            │ /home/user/        │
│   file-A.txt ✓     │            │   file-B.txt ✓     │
│   (their file)     │            │   (their file)     │
└─────────┬──────────┘            └─────────┬──────────┘
          │                                 │
    ┌─────▼─────┐                    ┌─────▼─────┐
    │  Upper 1  │                    │  Upper 2  │
    │  ~10MB    │                    │  ~25MB    │
    └─────┬─────┘                    └─────┬─────┘
          │                                 │
          └────────────┬────────────────────┘
                       │
                 ┌─────▼─────┐
                 │   Base    │
                 │  Layer    │
                 │  ~500MB   │
                 │ (shared)  │
                 └───────────┘
```

### Cost Profile

| Sessions | RAM (active) | Disk (filesystem) | Disk (snapshots) | Total |
|----------|-------------|-------------------|------------------|-------|
| 10 active | 1GB | ~200MB | 0 | ~1.2GB |
| 100 (10 active, 90 suspended) | 1GB | 2GB | 4.5GB | ~7.5GB |
| 1000 (10 active, 990 suspended) | 1GB | 20GB | 50GB | ~71GB |

Compare to **per-container approach**: 1000 sessions × 1GB = 1TB+ 

---

## Table of Contents

1. [Why OverlayFS?](#1-why-overlayfs)
2. [Architecture](#2-architecture)
3. [Implementation](#3-implementation)
4. [Integration with Multi-Display](#4-integration-with-multi-display)
5. [Integration with CRIU Snapshots](#5-integration-with-criu-snapshots)
6. [Storage Management](#6-storage-management)
7. [Security Considerations](#7-security-considerations)
8. [Limitations](#8-limitations)
9. [Implementation Plan](#9-implementation-plan)
10. [References](#10-references)

---

## 1. Why OverlayFS?

### What is OverlayFS?

OverlayFS is a **union filesystem** built into the Linux kernel (since 3.18). It merges multiple directory trees into a single unified view.

```bash
# Basic OverlayFS mount
mount -t overlay overlay \
  -o lowerdir=/base,upperdir=/session-1/upper,workdir=/session-1/work \
  /session-1/merged

# Session 1 now sees /session-1/merged as their root
# Reads: Check upper first, fall back to base
# Writes: Always go to upper (copy-on-write)
```

### Why It's Perfect for Sessions

| Feature | Benefit for Sessions |
|---------|---------------------|
| **Copy-on-Write** | Zero cost until files are written |
| **Shared base** | 500MB shared vs 500MB × N sessions |
| **Fast cleanup** | `rm -rf upper/` = session gone |
| **No kernel modules** | Built into Linux, works in Docker |
| **Snapshot-friendly** | Upper layer is just files, easy to backup |
| **Battle-tested** | Used by Docker itself for image layers |

### Comparison with Alternatives

| Approach | Disk Cost | RAM Cost | Isolation | Complexity |
|----------|-----------|----------|-----------|------------|
| **OverlayFS** ⭐ | ~0 (CoW) | ~0 | Medium | Low |
| Bind mounts | ~0 | ~0 | Weak | Very Low |
| Btrfs subvolumes | ~0 (CoW) | ~0 | Medium | Medium |
| Full containers | ~500MB+ | ~500MB+ | Strong | High |
| VM per session | ~2GB+ | ~1GB+ | Strongest | Very High |

---

## 2. Architecture

### Directory Structure

```
/sessions/
├── base/                           # Shared read-only base layer
│   ├── home/
│   │   └── user/
│   │       ├── .config/            # Default app configs
│   │       ├── .mozilla/           # Clean Firefox profile
│   │       └── Desktop/
│   └── tmp/                        # Empty template
│
├── active/                         # Currently running sessions
│   ├── session-abc123/
│   │   ├── upper/                  # OverlayFS upper (writable)
│   │   │   ├── home/               # Modified home files
│   │   │   └── tmp/                # Session temp files
│   │   ├── work/                   # OverlayFS workdir (required)
│   │   └── merged/                 # Mount point (what session sees)
│   │
│   └── session-def456/
│       ├── upper/
│       ├── work/
│       └── merged/
│
└── snapshots/                      # Suspended sessions (CRIU + filesystem)
    ├── session-xyz789/
    │   ├── criu/                   # CRIU checkpoint images
    │   └── filesystem.tar.zst      # Compressed upper layer
    └── ...
```

### Session Lifecycle with Filesystem Isolation

```
                    create_session()
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│  1. CREATE DIRECTORIES                                           │
│     mkdir -p /sessions/active/{id}/{upper,work,merged}           │
│                                                                   │
│  2. MOUNT OVERLAY                                                │
│     mount -t overlay overlay \                                   │
│       -o lowerdir=/sessions/base,\                               │
│          upperdir=/sessions/active/{id}/upper,\                  │
│          workdir=/sessions/active/{id}/work \                    │
│       /sessions/active/{id}/merged                               │
│                                                                   │
│  3. START DISPLAY (Xvfb + VNC)                                   │
│     With HOME=/sessions/active/{id}/merged/home/user             │
│                                                                   │
│  4. SESSION IS ACTIVE                                            │
│     - Agent runs with isolated filesystem view                   │
│     - Writes go to upper layer (CoW)                             │
│     - Base layer stays clean                                     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
     [SUSPEND]       [CONTINUE]      [DESTROY]
          │               │               │
          ▼               │               ▼
    CRIU dump +           │          umount overlay
    tar upper layer       │          rm -rf session dir
    umount overlay        │
          │               │
          ▼               │
    [SUSPENDED]           │
          │               │
          ▼               │
     [RESTORE] ◄──────────┘
          │
          ▼
    Recreate overlay
    CRIU restore
    [ACTIVE AGAIN]
```

---

## 3. Implementation

### 3.1 FilesystemManager Class

```python
# app/services/filesystem_manager.py

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional
import asyncio

class FilesystemManager:
    """
    Manages OverlayFS-based filesystem isolation for sessions.
    Each session gets a copy-on-write view of the base filesystem.
    """
    
    def __init__(
        self,
        sessions_dir: str = "/sessions",
        base_dir: str = "/sessions/base"
    ):
        self.sessions_dir = Path(sessions_dir)
        self.base_dir = Path(base_dir)
        self.active_dir = self.sessions_dir / "active"
        self.snapshots_dir = self.sessions_dir / "snapshots"
        
        # Ensure directories exist
        self.active_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_session_paths(self, session_id: str) -> dict:
        """Get all paths for a session."""
        session_root = self.active_dir / session_id
        return {
            "root": session_root,
            "upper": session_root / "upper",
            "work": session_root / "work",
            "merged": session_root / "merged",
        }
    
    async def create_session_filesystem(self, session_id: str) -> dict:
        """
        Create an isolated filesystem for a session using OverlayFS.
        
        Returns:
            dict with paths and status
        """
        paths = self._get_session_paths(session_id)
        
        # Create directories
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)
        
        # Mount OverlayFS
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
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"Failed to mount overlay: {stderr.decode()}")
        
        return {
            "session_id": session_id,
            "home_path": str(paths["merged"] / "home" / "user"),
            "tmp_path": str(paths["merged"] / "tmp"),
            "merged_root": str(paths["merged"]),
            "status": "mounted",
        }
    
    async def destroy_session_filesystem(self, session_id: str) -> bool:
        """Unmount and remove session filesystem."""
        paths = self._get_session_paths(session_id)
        
        # Unmount overlay
        try:
            proc = await asyncio.create_subprocess_exec(
                "umount", str(paths["merged"]),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
        except Exception:
            pass  # May already be unmounted
        
        # Remove session directory
        if paths["root"].exists():
            shutil.rmtree(paths["root"])
            return True
        return False
    
    async def archive_session_filesystem(
        self,
        session_id: str,
        compress: bool = True
    ) -> dict:
        """
        Archive the session's upper layer for snapshot storage.
        Called before CRIU suspend.
        
        Returns:
            dict with archive path and size
        """
        paths = self._get_session_paths(session_id)
        snapshot_dir = self.snapshots_dir / session_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        archive_name = "filesystem.tar.zst" if compress else "filesystem.tar"
        archive_path = snapshot_dir / archive_name
        
        # Unmount before archiving (CRIU will handle processes)
        await asyncio.create_subprocess_exec(
            "umount", str(paths["merged"])
        )
        
        # Archive upper layer
        if compress:
            cmd = ["tar", "-I", "zstd", "-cf", str(archive_path),
                   "-C", str(paths["upper"]), "."]
        else:
            cmd = ["tar", "-cf", str(archive_path),
                   "-C", str(paths["upper"]), "."]
        
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.communicate()
        
        # Clean up active directory
        shutil.rmtree(paths["root"])
        
        size = archive_path.stat().st_size
        return {
            "session_id": session_id,
            "archive_path": str(archive_path),
            "size_bytes": size,
            "size_mb": round(size / (1024 * 1024), 2),
            "compressed": compress,
        }
    
    async def restore_session_filesystem(self, session_id: str) -> dict:
        """
        Restore session filesystem from archive.
        Called before CRIU restore.
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
        if archive_path.suffix == ".zst" or ".tar.zst" in archive_path.name:
            cmd = ["tar", "-I", "zstd", "-xf", str(archive_path),
                   "-C", str(paths["upper"])]
        else:
            cmd = ["tar", "-xf", str(archive_path),
                   "-C", str(paths["upper"])]
        
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.communicate()
        
        # Mount overlay
        mount_cmd = [
            "mount", "-t", "overlay", "overlay",
            "-o", f"lowerdir={self.base_dir},"
                  f"upperdir={paths['upper']},"
                  f"workdir={paths['work']}",
            str(paths["merged"])
        ]
        
        proc = await asyncio.create_subprocess_exec(*mount_cmd)
        await proc.communicate()
        
        return {
            "session_id": session_id,
            "home_path": str(paths["merged"] / "home" / "user"),
            "status": "restored",
        }
    
    def get_session_disk_usage(self, session_id: str) -> Optional[dict]:
        """Get disk usage for a session's upper layer."""
        paths = self._get_session_paths(session_id)
        
        if not paths["upper"].exists():
            return None
        
        total_size = sum(
            f.stat().st_size
            for f in paths["upper"].rglob("*")
            if f.is_file()
        )
        
        return {
            "session_id": session_id,
            "size_bytes": total_size,
            "size_mb": round(total_size / (1024 * 1024), 2),
        }
```

### 3.2 Session Environment Setup

```python
# When launching session processes

def get_session_environment(session_id: str, fs_info: dict) -> dict:
    """
    Get environment variables for running processes in an isolated session.
    """
    return {
        # Filesystem isolation
        "HOME": fs_info["home_path"],
        "TMPDIR": fs_info["tmp_path"],
        "XDG_CONFIG_HOME": f"{fs_info['home_path']}/.config",
        "XDG_DATA_HOME": f"{fs_info['home_path']}/.local/share",
        "XDG_CACHE_HOME": f"{fs_info['home_path']}/.cache",
        
        # Display isolation (from DisplayManager)
        "DISPLAY": f":{display_num}",
        
        # Session identification
        "SESSION_ID": session_id,
    }
```

---

## 4. Integration with Multi-Display

The FilesystemManager integrates with the existing DisplayManager:

```python
# app/services/session_manager.py

class SessionManager:
    """
    Unified session management combining:
    - Display isolation (Xvfb/VNC)
    - Filesystem isolation (OverlayFS)
    - State persistence (CRIU snapshots)
    """
    
    def __init__(self):
        self.display_manager = DisplayManager()
        self.filesystem_manager = FilesystemManager()
        self.snapshot_manager = SnapshotManager()
        self.sessions: Dict[str, SessionInfo] = {}
    
    async def create_session(self, session_id: str) -> dict:
        """Create a fully isolated session."""
        
        # 1. Create isolated filesystem
        fs_info = await self.filesystem_manager.create_session_filesystem(
            session_id
        )
        
        # 2. Create isolated display
        display_info = await self.display_manager.create_display(
            session_id,
            env_overrides={
                "HOME": fs_info["home_path"],
                "TMPDIR": fs_info["tmp_path"],
            }
        )
        
        # 3. Track session
        self.sessions[session_id] = SessionInfo(
            id=session_id,
            status="active",
            display=display_info,
            filesystem=fs_info,
        )
        
        return {
            "session_id": session_id,
            "vnc_port": display_info["vnc_port"],
            "status": "active",
        }
    
    async def suspend_session(self, session_id: str) -> dict:
        """Suspend session to disk (display + filesystem + processes)."""
        
        info = self.sessions[session_id]
        
        # 1. CRIU checkpoint (saves process state)
        snapshot = await self.snapshot_manager.create_snapshot(
            session_id,
            info.display["xvfb_pid"]
        )
        
        # 2. Archive filesystem (saves file changes)
        fs_archive = await self.filesystem_manager.archive_session_filesystem(
            session_id
        )
        
        # 3. Update session state
        info.status = "suspended"
        
        return {
            "session_id": session_id,
            "status": "suspended",
            "snapshot_size_mb": snapshot["size_mb"],
            "filesystem_size_mb": fs_archive["size_mb"],
        }
    
    async def restore_session(self, session_id: str) -> dict:
        """Restore suspended session."""
        
        # 1. Restore filesystem first
        fs_info = await self.filesystem_manager.restore_session_filesystem(
            session_id
        )
        
        # 2. CRIU restore (brings back processes)
        process_info = await self.snapshot_manager.restore_snapshot(
            session_id
        )
        
        # 3. Update session state
        self.sessions[session_id].status = "active"
        
        return {
            "session_id": session_id,
            "status": "restored",
            "vnc_port": self.sessions[session_id].display["vnc_port"],
        }
```

---

## 5. Integration with CRIU Snapshots

### Suspend Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     SUSPEND SESSION                              │
│                                                                  │
│  1. CRIU DUMP                    2. ARCHIVE FILESYSTEM          │
│  ┌────────────────┐              ┌────────────────┐             │
│  │ Freeze Xvfb,   │              │ umount overlay │             │
│  │ Firefox, etc.  │              │                │             │
│  │                │              │ tar upper/     │             │
│  │ Save to:       │              │   → fs.tar.zst │             │
│  │ /snapshots/    │              │                │             │
│  │   {id}/criu/   │              │ rm active/{id} │             │
│  └────────────────┘              └────────────────┘             │
│           │                              │                       │
│           └──────────────┬───────────────┘                       │
│                          ▼                                       │
│                  /snapshots/{session_id}/                        │
│                  ├── criu/                                       │
│                  │   ├── core-*.img                              │
│                  │   ├── mm-*.img                                │
│                  │   └── pages-*.img                             │
│                  └── filesystem.tar.zst                          │
│                                                                  │
│                  RAM: 0 MB (session fully on disk)               │
└─────────────────────────────────────────────────────────────────┘
```

### Restore Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     RESTORE SESSION                              │
│                                                                  │
│  1. RESTORE FILESYSTEM           2. CRIU RESTORE                │
│  ┌────────────────┐              ┌────────────────┐             │
│  │ mkdir active/  │              │ Restore from   │             │
│  │   {id}/        │              │ criu/*.img     │             │
│  │                │              │                │             │
│  │ extract        │              │ Processes      │             │
│  │ fs.tar.zst     │              │ resume exactly │             │
│  │   → upper/     │              │ where they     │             │
│  │                │              │ were           │             │
│  │ mount overlay  │              │                │             │
│  └────────────────┘              └────────────────┘             │
│           │                              │                       │
│           └──────────────┬───────────────┘                       │
│                          ▼                                       │
│                  Session Active Again                            │
│                  - Same Firefox tabs                             │
│                  - Same files in ~/Downloads                     │
│                  - Exact process state                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Storage Management

### 6.1 Disk Usage Patterns

| Session Activity | Upper Layer Size | Typical Contents |
|-----------------|------------------|------------------|
| Just created | ~0 MB | Empty |
| Light browsing | 5-20 MB | Browser cache, cookies |
| Downloaded files | 20-100 MB | PDFs, images |
| Heavy use | 100-500 MB | Large downloads, app data |
| Development | 500MB-2GB | Code repos, node_modules |

### 6.2 Quotas

```python
class FilesystemManager:
    DEFAULT_QUOTA_MB = 500  # Per-session limit
    
    async def check_quota(self, session_id: str) -> dict:
        """Check if session is within disk quota."""
        usage = self.get_session_disk_usage(session_id)
        
        return {
            "session_id": session_id,
            "used_mb": usage["size_mb"],
            "quota_mb": self.DEFAULT_QUOTA_MB,
            "remaining_mb": self.DEFAULT_QUOTA_MB - usage["size_mb"],
            "over_quota": usage["size_mb"] > self.DEFAULT_QUOTA_MB,
        }
    
    async def enforce_quota(self, session_id: str):
        """Called before allowing new downloads/writes."""
        quota = await self.check_quota(session_id)
        
        if quota["over_quota"]:
            raise QuotaExceededError(
                f"Session {session_id} over quota: "
                f"{quota['used_mb']}MB / {quota['quota_mb']}MB"
            )
```

### 6.3 Cleanup Strategy

```python
async def cleanup_expired_sessions(
    max_suspended_age_hours: int = 24,
    max_total_storage_gb: float = 50.0
):
    """
    Clean up old suspended sessions to free disk space.
    
    Priority:
    1. Delete sessions older than max_suspended_age_hours
    2. If still over quota, delete largest sessions first
    """
    now = time.time()
    sessions = []
    
    # Collect all suspended sessions
    for session_dir in snapshots_dir.iterdir():
        if not session_dir.is_dir():
            continue
        
        mtime = session_dir.stat().st_mtime
        age_hours = (now - mtime) / 3600
        
        # Calculate total size (CRIU + filesystem)
        size = sum(f.stat().st_size for f in session_dir.rglob("*"))
        
        sessions.append({
            "id": session_dir.name,
            "path": session_dir,
            "age_hours": age_hours,
            "size_bytes": size,
        })
    
    # Delete old sessions
    for s in sessions:
        if s["age_hours"] > max_suspended_age_hours:
            shutil.rmtree(s["path"])
            logger.info(f"Deleted expired session: {s['id']}")
    
    # Check total storage
    total_bytes = sum(s["size_bytes"] for s in sessions)
    max_bytes = max_total_storage_gb * 1024**3
    
    if total_bytes > max_bytes:
        # Delete largest first until under quota
        sessions.sort(key=lambda x: x["size_bytes"], reverse=True)
        for s in sessions:
            if total_bytes <= max_bytes:
                break
            shutil.rmtree(s["path"])
            total_bytes -= s["size_bytes"]
            logger.info(f"Deleted large session: {s['id']} ({s['size_bytes']})")
```

---

## 7. Security Considerations

### 7.1 Isolation Boundaries

| Component | Isolated? | Notes |
|-----------|-----------|-------|
| **Display (X11)** | ✅ Yes | Separate Xvfb per session |
| **Filesystem view** | ✅ Yes | OverlayFS merged view |
| **Processes** | ⚠️ Partial | Same PID namespace |
| **Network** | ❌ No | Shared network namespace |
| **CPU/Memory** | ❌ No | No cgroups (could add) |

### 7.2 What OverlayFS Does NOT Protect Against

⚠️ **Important limitations:**

1. **Process visibility** - Sessions can see each other's processes via `/proc`
2. **Network sniffing** - Sessions share network, could sniff traffic
3. **Resource exhaustion** - One session could starve others
4. **Kernel exploits** - Shared kernel surface

### 7.3 Hardening Options

```python
# Additional isolation with mount namespaces
async def create_hardened_session(session_id: str):
    """Create session with additional namespace isolation."""
    
    # Use unshare to create new mount namespace
    cmd = [
        "unshare",
        "--mount",           # New mount namespace
        "--pid",             # New PID namespace (can't see other processes)
        "--fork",            # Fork into new namespace
        "--mount-proc",      # Mount new /proc
        "--",
        "start-session.sh", session_id
    ]
```

### 7.4 Sensitive Data in Snapshots

⚠️ **Same warning as CRIU snapshots:**

Filesystem archives contain:
- Browser cookies/sessions
- Downloaded files
- Any credentials stored in files
- `.bash_history`

**Mitigations:**
- Encrypt archives at rest
- Set restrictive permissions (0600)
- Auto-delete after TTL
- Don't backup without encryption

---

## 8. Limitations

### 8.1 Docker Requirements

**Important clarification:** OverlayFS is a **kernel feature**, not a package to install. Any Linux host running Docker already has OverlayFS - Docker itself uses it for image layers!

The only requirement is **permissions** in docker-compose.yml:

```yaml
# docker-compose.yml
services:
  app:
    cap_add:
      - SYS_ADMIN     # Required for mount operations
    security_opt:
      - apparmor:unconfined  # Required for mount syscall
```

**Note:** The entrypoint.sh script tests mount permissions on startup and exits with a clear error if CAP_SYS_ADMIN is missing. If Docker runs on your host, OverlayFS is guaranteed to be available.

### 8.2 Filesystem Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| **No hardlinks across layers** | Some apps may fail | Usually not an issue |
| **Copy-up on modify** | Large files = slow first write | Pre-copy large templates |
| **Inode exhaustion** | Many small files = issues | Monitor and set limits |
| **No cross-session sharing** | Can't share files between sessions | Use explicit export API |

### 8.3 Known Issues

1. **Firefox profile locking** - May need to copy profile instead of overlay
2. **Large Chrome/Chromium profiles** - Initial writes can be slow
3. **SQLite databases** - WAL mode may have issues (use different journal mode)

---

## 9. Implementation Plan

### Phase 1: Basic OverlayFS Isolation

| Task | Effort |
|------|--------|
| Create FilesystemManager class | 2-3 hours |
| Integrate with session creation | 1-2 hours |
| Update agent to use session paths | 1 hour |
| Test with Firefox | 2 hours |
| **Total Phase 1** | **6-8 hours** |

### Phase 2: Snapshot Integration

| Task | Effort |
|------|--------|
| Archive/restore functions | 2-3 hours |
| Integrate with CRIU suspend/restore | 2-3 hours |
| Test full suspend/restore cycle | 2 hours |
| **Total Phase 2** | **6-8 hours** |

### Phase 3: Production Hardening

| Task | Effort |
|------|--------|
| Quota enforcement | 1-2 hours |
| Cleanup automation | 1-2 hours |
| Monitoring/metrics | 2-3 hours |
| Namespace hardening (optional) | 3-4 hours |
| **Total Phase 3** | **7-11 hours** |

### Total Estimated Effort

| Phase | Hours |
|-------|-------|
| Phase 1 (MVP) | 6-8 |
| Phase 2 (Snapshots) | 6-8 |
| Phase 3 (Production) | 7-11 |
| **Total** | **19-27 hours** |

---

## 10. References

### OverlayFS
- [Kernel Documentation](https://www.kernel.org/doc/html/latest/filesystems/overlayfs.html)
- [Docker Storage Drivers](https://docs.docker.com/storage/storagedriver/overlayfs-driver/)

### Namespace Isolation
- [unshare(1) man page](https://man7.org/linux/man-pages/man1/unshare.1.html)
- [Linux Namespaces](https://man7.org/linux/man-pages/man7/namespaces.7.html)

### Related Projects
- [Bubblewrap](https://github.com/containers/bubblewrap) - Unprivileged sandboxing
- [Firejail](https://firejail.wordpress.com/) - SUID sandbox program

---

## Appendix A: Docker Configuration

```dockerfile
# Dockerfile additions for OverlayFS support

FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    zstd \           # For compressed archives
    fuse-overlayfs   # Alternative if kernel overlay unavailable

# Create base filesystem template
COPY base-template/ /sessions/base/

# Set up proper permissions
RUN chmod 755 /sessions && \
    chmod 755 /sessions/base
```

```yaml
# docker-compose.yml
services:
  computer-use:
    build: .
    privileged: true
    volumes:
      - sessions-data:/sessions
    
volumes:
  sessions-data:
    driver: local
```

---

## Appendix B: Cost Calculator

```python
def calculate_storage_costs(
    total_users: int,
    concurrent_sessions: int,
    avg_filesystem_mb: float = 50,
    avg_snapshot_mb: float = 100,
    storage_cost_per_gb: float = 0.10  # $/GB/month
) -> dict:
    """
    Calculate estimated storage costs.
    
    Example:
    - 1000 users
    - 10 concurrent (active)
    - 990 suspended
    """
    
    # Active sessions: RAM + small disk
    active_ram_gb = concurrent_sessions * 0.1  # 100MB each
    active_disk_gb = concurrent_sessions * (avg_filesystem_mb / 1024)
    
    # Suspended sessions: disk only
    suspended_sessions = total_users - concurrent_sessions
    suspended_disk_gb = suspended_sessions * (avg_snapshot_mb / 1024)
    
    # Base layer (shared)
    base_layer_gb = 0.5
    
    total_disk_gb = base_layer_gb + active_disk_gb + suspended_disk_gb
    monthly_cost = total_disk_gb * storage_cost_per_gb
    
    return {
        "active_sessions": concurrent_sessions,
        "suspended_sessions": suspended_sessions,
        "total_disk_gb": round(total_disk_gb, 2),
        "monthly_cost_usd": round(monthly_cost, 2),
        "cost_per_user_usd": round(monthly_cost / total_users, 4),
    }

# Example
print(calculate_storage_costs(1000, 10))
# {'active_sessions': 10, 'suspended_sessions': 990, 
#  'total_disk_gb': 97.34, 'monthly_cost_usd': 9.73, 
#  'cost_per_user_usd': 0.0097}
```

---

*This document describes a future enhancement for filesystem isolation. Combined with Multi-Display and CRIU snapshots, it provides a complete solution for cheap, scalable, semi-isolated sessions.*
