# Session Snapshots: CRIU-Based State Persistence

> ⚠️ **Context**: See [`MASTER_ROADMAP.md`](./MASTER_ROADMAP.md) for project overview.

**Author:** Pablo Schaffner  
**Date:** December 2025  
**Status:** 🔮 Future Research  
**Category:** Open Source Core Enhancement  
**Depends on:** [Multi-Session Scaling](./multi_session_scaling.md)

---

## Executive Summary

### The Problem

With Multi-Display architecture, each active session consumes resources (~100-200MB RAM). If users are inactive for extended periods, we're wasting resources keeping their displays running.

### The Solution

Use **CRIU (Checkpoint/Restore In Userspace)** to:
1. Freeze a session's processes
2. Save complete state to disk
3. Free resources (terminate processes)
4. Restore exact state when user returns

```
ACTIVE SESSION              SUSPENDED                    RESTORED
┌─────────────────┐        ┌─────────────────┐         ┌─────────────────┐
│ Xvfb :1         │        │                 │         │ Xvfb :1         │
│ ├── Firefox     │  CRIU  │  /snapshots/    │  CRIU   │ ├── Firefox     │
│ │   └── tabs... │ ─────► │    session-123/ │ ──────► │ │   └── tabs... │
│ └── Terminal    │  dump  │    ├── pages/   │ restore │ └── Terminal    │
└─────────────────┘        │    └── core...  │         └─────────────────┘
     ~200MB RAM                  ~500MB disk                ~200MB RAM
                           (0 MB RAM while suspended)
```

---

## Table of Contents

1. [What is CRIU?](#1-what-is-criu)
2. [How CRIU Works](#2-how-criu-works)
3. [Integration with Multi-Display](#3-integration-with-multi-display)
4. [Implementation](#4-implementation)
5. [Limitations & Challenges](#5-limitations--challenges)
6. [Security Considerations](#6-security-considerations)
7. [Storage Management](#7-storage-management)
8. [Implementation Plan](#8-implementation-plan)
9. [References](#9-references)

---

## 1. What is CRIU?

**CRIU** (Checkpoint/Restore In Userspace) is a Linux software that allows you to:

- **Freeze** a running process (or process tree)
- **Save** its complete state to files
- **Restore** the process later, exactly as it was

### What Gets Saved?

| Component | Saved? | Details |
|-----------|--------|---------|
| Memory pages | ✅ Yes | All process memory |
| CPU registers | ✅ Yes | Exact execution state |
| File descriptors | ✅ Yes | Open files, sockets |
| File positions | ✅ Yes | Seek positions in files |
| Pipes | ✅ Yes | Inter-process pipes |
| Unix sockets | ✅ Yes | Local socket connections |
| TCP connections | ⚠️ Partial | With --tcp-established |
| Timers | ✅ Yes | Process timers |
| Signal handlers | ✅ Yes | Signal state |
| Process tree | ✅ Yes | Parent/child relationships |

### Use Cases

- **Live migration** - Move running processes between machines
- **Container checkpointing** - Docker/Podman checkpoint support
- **Fast startup** - Pre-warmed application snapshots
- **Testing** - Snapshot → test → restore → test again
- **Resource management** - Suspend idle processes (our use case!)

---

## 2. How CRIU Works

### Basic Commands

```bash
# Checkpoint a process tree
criu dump --tree <PID> --images-dir /snapshots/session-123/

# Restore from checkpoint
criu restore --images-dir /snapshots/session-123/
```

### What Happens During Dump

```
1. FREEZE        2. COLLECT         3. DUMP           4. CLEANUP
┌─────────┐     ┌─────────┐        ┌─────────┐       ┌─────────┐
│ Process │     │ Process │        │ Process │       │         │
│ Running │ ──► │ Frozen  │ ─────► │ Frozen  │ ────► │ (dead)  │
│         │     │ +seized │        │ +dumped │       │         │
└─────────┘     └─────────┘        └─────────┘       └─────────┘
                                        │
                                        ▼
                               /snapshots/session-123/
                               ├── core-1.img
                               ├── mm-1.img (memory)
                               ├── pages-1.img
                               ├── files.img
                               └── ...
```

### What Happens During Restore

```
1. READ IMAGES   2. CREATE         3. RESTORE        4. RESUME
┌─────────────┐  ┌─────────┐      ┌─────────┐       ┌─────────┐
│ /snapshots/ │  │ Process │      │ Process │       │ Process │
│ session-123/│► │ Created │ ───► │ Memory  │ ────► │ Running │
│ *.img files │  │ (empty) │      │ Restored│       │ (exact) │
└─────────────┘  └─────────┘      └─────────┘       └─────────┘
```

---

## 3. Integration with Multi-Display

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Single Docker Container                         │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     FastAPI Backend                          │   │
│  │                    Display Manager                           │   │
│  │                   Snapshot Manager  ◄── NEW                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│  │   Xvfb :1     │  │  (suspended)  │  │   Xvfb :3     │          │
│  │   Session 1   │  │   Session 2   │  │   Session 3   │          │
│  │   ACTIVE      │  │   SNAPSHOT    │  │   ACTIVE      │          │
│  │   ~200MB      │  │   on disk     │  │   ~200MB      │          │
│  └───────────────┘  └───────────────┘  └───────────────┘          │
│                            │                                        │
│                            ▼                                        │
│                     /snapshots/session-2/                           │
│                     ├── core-*.img                                  │
│                     ├── mm-*.img                                    │
│                     └── pages-*.img                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Session States

```
                    create_display()
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│     ┌──────────┐      suspend()      ┌───────────┐              │
│     │  ACTIVE  │ ─────────────────► │ SUSPENDED │              │
│     │          │                     │           │              │
│     │ Xvfb+apps│      restore()      │ Snapshot  │              │
│     │ running  │ ◄───────────────── │ on disk   │              │
│     └──────────┘                     └───────────┘              │
│          │                                 │                     │
│          │ destroy()                       │ destroy()           │
│          ▼                                 ▼                     │
│     ┌──────────┐                     ┌───────────┐              │
│     │ DESTROYED│                     │ DESTROYED │              │
│     │          │                     │           │              │
│     └──────────┘                     └───────────┘              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Implementation

### 4.1 SnapshotManager Class

```python
# app/services/snapshot_manager.py

import subprocess
import os
import shutil
from pathlib import Path
from typing import Optional
import asyncio

class SnapshotManager:
    """
    Manages CRIU-based session snapshots.
    Allows suspending and restoring entire display sessions.
    """
    
    def __init__(self, snapshots_dir: str = "/snapshots"):
        self.snapshots_dir = Path(snapshots_dir)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_snapshot_path(self, session_id: str) -> Path:
        return self.snapshots_dir / session_id
    
    async def create_snapshot(
        self, 
        session_id: str, 
        root_pid: int,
        compress: bool = True
    ) -> dict:
        """
        Checkpoint a running session to disk.
        
        Args:
            session_id: Unique session identifier
            root_pid: PID of the root process (Xvfb or session wrapper)
            compress: Whether to compress checkpoint images
        
        Returns:
            dict with snapshot info (path, size, etc.)
        """
        snapshot_path = self._get_snapshot_path(session_id)
        
        # Clean previous snapshot if exists
        if snapshot_path.exists():
            shutil.rmtree(snapshot_path)
        snapshot_path.mkdir(parents=True)
        
        # Build CRIU command
        cmd = [
            "criu", "dump",
            "--tree", str(root_pid),
            "--images-dir", str(snapshot_path),
            "--leave-stopped",      # Don't kill, just stop (we'll kill after)
            "--shell-job",          # Handle shell sessions
            "--file-locks",         # Save file locks
            "--tcp-established",    # Try to save TCP connections
            "--ext-unix-sk",        # Handle external Unix sockets
        ]
        
        if compress:
            cmd.append("--compress")
        
        # Run CRIU dump
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"CRIU dump failed: {stderr.decode()}")
        
        # Kill the process tree (CRIU left it stopped)
        os.kill(root_pid, 9)
        
        # Calculate snapshot size
        total_size = sum(
            f.stat().st_size for f in snapshot_path.rglob("*") if f.is_file()
        )
        
        return {
            "session_id": session_id,
            "path": str(snapshot_path),
            "size_bytes": total_size,
            "size_mb": round(total_size / (1024 * 1024), 2),
            "compressed": compress,
        }
    
    async def restore_snapshot(self, session_id: str) -> dict:
        """
        Restore a session from snapshot.
        
        Returns:
            dict with new PID and status
        """
        snapshot_path = self._get_snapshot_path(session_id)
        
        if not snapshot_path.exists():
            raise FileNotFoundError(f"No snapshot for session {session_id}")
        
        # Build CRIU restore command
        cmd = [
            "criu", "restore",
            "--images-dir", str(snapshot_path),
            "--shell-job",
            "--file-locks",
            "--tcp-established",
            "--ext-unix-sk",
            "-d",  # Detach (daemonize)
            "--pidfile", str(snapshot_path / "restored.pid"),
        ]
        
        # Run CRIU restore
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"CRIU restore failed: {stderr.decode()}")
        
        # Read the new PID
        pid_file = snapshot_path / "restored.pid"
        new_pid = int(pid_file.read_text().strip())
        
        return {
            "session_id": session_id,
            "pid": new_pid,
            "status": "restored",
        }
    
    async def delete_snapshot(self, session_id: str) -> bool:
        """Delete a snapshot from disk."""
        snapshot_path = self._get_snapshot_path(session_id)
        
        if snapshot_path.exists():
            shutil.rmtree(snapshot_path)
            return True
        return False
    
    def get_snapshot_info(self, session_id: str) -> Optional[dict]:
        """Get info about an existing snapshot."""
        snapshot_path = self._get_snapshot_path(session_id)
        
        if not snapshot_path.exists():
            return None
        
        total_size = sum(
            f.stat().st_size for f in snapshot_path.rglob("*") if f.is_file()
        )
        
        return {
            "session_id": session_id,
            "path": str(snapshot_path),
            "size_bytes": total_size,
            "size_mb": round(total_size / (1024 * 1024), 2),
        }
```

### 4.2 DisplayManager Integration

```python
# In display_manager.py

class DisplayManager:
    def __init__(self):
        self.displays: Dict[str, dict] = {}
        self.snapshot_manager = SnapshotManager()
    
    async def suspend_display(self, session_id: str) -> dict:
        """
        Suspend a display by checkpointing it with CRIU.
        Frees all RAM, keeps state on disk.
        """
        if session_id not in self.displays:
            raise ValueError(f"Session {session_id} not found")
        
        info = self.displays[session_id]
        root_pid = info["xvfb_pid"]  # Or wrapper process PID
        
        # Create CRIU checkpoint
        snapshot = await self.snapshot_manager.create_snapshot(
            session_id, root_pid
        )
        
        # Update session state
        info["status"] = "suspended"
        info["snapshot"] = snapshot
        
        # Clear PIDs (processes are dead)
        info["xvfb_pid"] = None
        info["vnc_pid"] = None
        
        return snapshot
    
    async def restore_display(self, session_id: str) -> dict:
        """
        Restore a suspended display from CRIU checkpoint.
        """
        if session_id not in self.displays:
            raise ValueError(f"Session {session_id} not found")
        
        info = self.displays[session_id]
        
        if info.get("status") != "suspended":
            raise ValueError(f"Session {session_id} is not suspended")
        
        # Restore from CRIU checkpoint
        result = await self.snapshot_manager.restore_snapshot(session_id)
        
        # Update session state
        info["status"] = "active"
        info["xvfb_pid"] = result["pid"]
        # Note: VNC and other PIDs may need to be re-discovered
        
        return result
```

### 4.3 API Endpoints

```python
# In routes/sessions.py

@router.post("/sessions/{session_id}/suspend")
async def suspend_session(session_id: str):
    """Suspend a session, freeing resources."""
    snapshot = await display_manager.suspend_display(session_id)
    return {
        "status": "suspended",
        "snapshot_size_mb": snapshot["size_mb"],
    }

@router.post("/sessions/{session_id}/restore")
async def restore_session(session_id: str):
    """Restore a suspended session."""
    result = await display_manager.restore_display(session_id)
    return {
        "status": "restored",
        "vnc_port": display_manager.displays[session_id]["vnc_port"],
    }
```

---

## 5. Limitations & Challenges

### 5.1 Kernel Requirements

CRIU requires kernel support:
```bash
# Check if kernel supports CRIU
grep CONFIG_CHECKPOINT_RESTORE /boot/config-$(uname -r)
# Should show: CONFIG_CHECKPOINT_RESTORE=y
```

Most modern Linux kernels (4.x+) have this enabled.

### 5.2 Container Capabilities

The container needs elevated privileges:

```yaml
# docker-compose.yml
services:
  app:
    cap_add:
      - SYS_PTRACE      # Required for process tracing
      - SYS_ADMIN       # Required for namespace operations
    security_opt:
      - apparmor:unconfined  # May be needed
```

### 5.3 Known Issues

| Issue | Impact | Workaround |
|-------|--------|------------|
| **External TCP connections** | Browser connections may break | Use --tcp-established, reconnect logic |
| **GPU/WebGL state** | Not saved | Apps using GPU may have visual glitches |
| **Shared memory (shm)** | Complex to restore | Use --enable-fs shmem |
| **Unix sockets to external** | May not restore | Use --ext-unix-sk |
| **AIO (async I/O)** | Limited support | May fail with some apps |
| **Large memory** | Big checkpoint files | Use --compress |

### 5.4 Applications That May Have Issues

| Application | Issue | Notes |
|-------------|-------|-------|
| Firefox | TCP connections | Reconnects automatically |
| Chrome | More GPU-dependent | May have more issues |
| Apps using D-Bus | External connections | May need restart |
| Apps with GPU rendering | GPU state not saved | Visual glitches |

---

## 6. Security Considerations

### 6.1 Sensitive Data in Snapshots

⚠️ **Snapshots contain process memory!**

This includes:
- Passwords in memory
- Session tokens
- API keys
- Any sensitive data the app was processing

### 6.2 Mitigations

```python
# Encrypt snapshots at rest
async def create_snapshot(self, session_id: str, root_pid: int):
    # ... create snapshot ...
    
    # Encrypt the snapshot directory
    await self._encrypt_snapshot(snapshot_path, encryption_key)

# Access control
def _get_snapshot_path(self, session_id: str) -> Path:
    path = self.snapshots_dir / session_id
    # Ensure restrictive permissions
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    return path
```

### 6.3 Recommendations

1. **Encrypt snapshots** at rest
2. **Restrict access** to /snapshots directory
3. **Auto-delete** old snapshots after TTL
4. **Audit logging** for snapshot operations
5. **Don't backup** snapshot directory without encryption

---

## 7. Storage Management

### 7.1 Expected Sizes

| Session Type | Active RAM | Snapshot Size (compressed) |
|--------------|------------|---------------------------|
| Minimal (Xvfb only) | ~50MB | ~20MB |
| Browser + light use | ~200MB | ~80MB |
| Browser + heavy use | ~500MB | ~200MB |
| Complex workflow | ~1GB+ | ~400MB+ |

### 7.2 Cleanup Strategy

```python
class SnapshotManager:
    async def cleanup_old_snapshots(
        self, 
        max_age_hours: int = 24,
        max_total_size_gb: float = 10.0
    ):
        """Clean up old/excess snapshots."""
        now = time.time()
        snapshots = []
        
        for session_dir in self.snapshots_dir.iterdir():
            if not session_dir.is_dir():
                continue
            
            size = sum(f.stat().st_size for f in session_dir.rglob("*"))
            mtime = session_dir.stat().st_mtime
            age_hours = (now - mtime) / 3600
            
            snapshots.append({
                "path": session_dir,
                "size": size,
                "age_hours": age_hours,
            })
        
        # Delete old snapshots
        for snap in snapshots:
            if snap["age_hours"] > max_age_hours:
                shutil.rmtree(snap["path"])
        
        # If still over quota, delete largest first
        total_size = sum(s["size"] for s in snapshots)
        if total_size > max_total_size_gb * 1024**3:
            snapshots.sort(key=lambda x: x["size"], reverse=True)
            for snap in snapshots:
                if total_size <= max_total_size_gb * 1024**3:
                    break
                shutil.rmtree(snap["path"])
                total_size -= snap["size"]
```

---

## 8. Implementation Plan

### Phase 1: Basic CRIU Integration
| Task | Effort |
|------|--------|
| Add CRIU to Docker image | 1 hour |
| Implement SnapshotManager | 2-3 hours |
| Add suspend/restore to DisplayManager | 2 hours |
| API endpoints | 1 hour |
| **Total Phase 1** | **6-7 hours** |

### Phase 2: Production Hardening
| Task | Effort |
|------|--------|
| Snapshot encryption | 2-3 hours |
| Auto-cleanup | 1-2 hours |
| Error handling & recovery | 2-3 hours |
| Testing with various apps | 3-4 hours |
| **Total Phase 2** | **8-12 hours** |

### Phase 3: Auto-Suspend (Optional)
| Task | Effort |
|------|--------|
| Idle detection | 2-3 hours |
| Auto-suspend on idle | 1-2 hours |
| Auto-restore on access | 1-2 hours |
| **Total Phase 3** | **4-7 hours** |

---

## 9. References

### Official Documentation
- [CRIU Official Site](https://criu.org/)
- [CRIU Wiki](https://criu.org/Main_Page)
- [CRIU GitHub](https://github.com/checkpoint-restore/criu)

### Docker Integration
- [Docker Checkpoint/Restore (Experimental)](https://docs.docker.com/engine/reference/commandline/checkpoint/)
- [Podman Checkpoint](https://docs.podman.io/en/latest/markdown/podman-container-checkpoint.1.html)

### Related Projects
- [DMTCP](https://dmtcp.sourceforge.io/) - Alternative checkpoint/restore tool
- [go-criu](https://github.com/checkpoint-restore/go-criu) - Go bindings for CRIU

---

*This document describes a future enhancement. CRIU-based snapshots are not required for MVP but provide significant resource savings for multi-session deployments.*

