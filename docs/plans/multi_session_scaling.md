# Multi-Session & Concurrent Users Architecture Plan

**Author:** Pablo Schaffner  
**Date:** December 2025 
**Status:** Proposed Architecture

---

## Executive Summary

### The Problem
Our current implementation has **one desktop** shared by all sessions. When User B uses the system, User A's browser tabs, forms, and visual state are **destroyed**.

### The Solution
Use **Multiple X11 Displays** within a single container. Each session gets its own virtual framebuffer (Xvfb) with isolated desktop state.

### Key Architecture Decision

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Single Docker Container                         │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     FastAPI Backend                          │   │
│  │                    Display Manager                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│  │   Xvfb :1     │  │   Xvfb :2     │  │   Xvfb :3     │   ...    │
│  │   Session 1   │  │   Session 2   │  │   Session 3   │          │
│  │   Firefox     │  │   Firefox     │  │   Firefox     │          │
│  │   VNC :5901   │  │   VNC :5902   │  │   VNC :5903   │          │
│  └───────────────┘  └───────────────┘  └───────────────┘          │
│                                                                      │
│  Each session: ~100MB RAM, 1-3 second startup                       │
└─────────────────────────────────────────────────────────────────────┘
```

### User Experience
```bash
# Single command to start
docker-compose up

# Everything else is automatic:
# - Session creation starts new Xvfb display + VNC
# - Each user gets isolated X11 desktop  
# - Sessions persist while processes run
# - Works on Render.com (no Docker socket needed!)
```

### Why Multi-Display Over Container Orchestration?

| Factor | Multi-Display ⭐ | Container Orchestration |
|--------|-----------------|------------------------|
| RAM per session | ~100MB | ~1GB |
| Session startup | 1-3 seconds | 10-30 seconds |
| Render.com compatible | ✅ Yes | ❌ No (needs docker.sock) |
| Complexity | Low | Medium-High |
| Good for demo? | ✅ Perfect | Overkill |

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Current Architecture Limitations](#2-current-architecture-limitations)
3. [Multi-User Models](#3-multi-user-models)
4. [Solution: Multiple X11 Displays](#4-solution-multiple-x11-displays-single-container)
5. [Implementation Details](#5-implementation-details)
6. [Implementation Plan](#6-implementation-plan)
7. [Future: Multi-Agent Collaboration](#7-future-multi-agent-collaboration)
8. [References](#8-references)

---

## 1. Problem Statement

### 1.1 The Concurrency Problem

The current implementation supports **one active session at a time** because:

- Each session requires control of a virtual desktop (X11)
- There is only **one virtual display** (`:1`) in the container
- The AI agent controls **one mouse, one keyboard, one screen**
- Concurrent agent commands would conflict on the same desktop

### 1.2 The State Persistence Problem (Critical!)

**Scenario:**
```
Timeline:
─────────────────────────────────────────────────────────────────►

User A: Creates Session 1
        │
        ▼
        Agent opens Firefox, navigates to site, fills form...
        Desktop State: [Firefox with filled form]
        │
        │      User B: Creates Session 2
        │              │
        │              ▼
        │              Agent opens new Firefox, does different task...
        │              Desktop State: [OVERWRITTEN - User A's state LOST!]
        │
        ▼
User A: "Continue my session"
        │
        ▼
        ERROR: Previous state is GONE ❌
        The form, browser tabs, everything User A did is destroyed.
```

**Why this happens:**
- There is only ONE desktop (X11 display `:1`)
- Sessions share the same desktop environment
- No state isolation between sessions
- Chat history is saved, but **desktop state is not**

**Impact:**
- Users cannot resume sessions reliably
- Multi-user scenarios are broken
- Even single-user "pause and resume later" is broken

**Goal:** Enable multiple users to run independent, isolated computer-use sessions simultaneously, each with **persistent desktop state**.

### 1.3 Current Implementation Behavior (Q&A)

**Q: With the current implementation, what happens if User A creates a session, uses it, then User B creates a new session and does other things, and then User A wants to continue?**

**A: User A's desktop state is LOST.** Here's why:

```
Current Implementation (Single Container):
┌─────────────────────────────────────────────────────────────────┐
│                    Single Docker Container                       │
│                                                                  │
│   ┌────────────────────────────────────────────────────────┐   │
│   │              Single X11 Display (:1)                    │   │
│   │                                                         │   │
│   │   [Firefox]  [Terminal]  [Files]  ← Only ONE desktop   │   │
│   │                                                         │   │
│   └────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Session 1 (User A): DB record exists, chat history saved     │
│   Session 2 (User B): DB record exists, chat history saved     │
│                                                                  │
│   BUT: Both sessions share THE SAME X11 desktop!               │
│        User B's actions OVERWRITE User A's visual state.       │
└─────────────────────────────────────────────────────────────────┘
```

**What IS preserved:**
- ✅ Session metadata (title, model, created_at)
- ✅ Chat history (all messages in/out)
- ✅ Tool use history (what the agent did)

**What is NOT preserved:**
- ❌ Browser state (tabs, cookies, form data)
- ❌ Open applications
- ❌ Desktop layout
- ❌ Any files created in the session
- ❌ Clipboard contents

**Practical Impact:**
```
User A: "Go to amazon.com, search for laptops, add one to cart"
        Agent: Opens Firefox, searches, adds to cart
        Desktop state: Firefox with cart showing laptop
        
User B: "Go to google.com and search for weather"
        Agent: Opens NEW Firefox window (or navigates away)
        Desktop state: Firefox showing weather search
        
User A: "Now checkout my cart"
        Agent: Takes screenshot... sees weather search, NOT cart!
        Agent is confused, session context is broken
```

**This is a fundamental architectural limitation, not a bug.**

---

## 2. Current Architecture Limitations

```
┌─────────────────────────────────────────────────────┐
│              Single Docker Container                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   FastAPI   │  │  X11 (:1)   │  │    VNC      │ │
│  │   Backend   │  │   Display   │  │   Server    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│  ┌─────────────┐  ┌─────────────┐                  │
│  │   Agent     │  │   Firefox   │                  │
│  │   Runner    │  │   Browser   │                  │
│  └─────────────┘  └─────────────┘                  │
└─────────────────────────────────────────────────────┘
         ↑                    ↑
    Session A            Session B
    (works ✅)           (blocked ❌)
```

**Limitation:** Only one session can actively control the desktop at any time.

---

## 3. Multi-User Models

There are two distinct multi-user scenarios:

### Model A: Collaborative Viewing (Same Session)
Multiple users **watch and interact with the same session** simultaneously.

```
User A ─────┐
            ├──→ [Single Session] ──→ [Single Desktop]
User B ─────┘
```

- **Use case:** Watch parties, pair programming, support sessions
- **Complexity:** Low - single container, multiple viewers

### Model B: Isolated Sessions (Our Need)
Each user has their **own independent session** with a separate desktop.

```
User A ──→ [Session A] ──→ [Desktop A]
User B ──→ [Session B] ──→ [Desktop B]
User C ──→ [Session C] ──→ [Desktop C]
```

- **Use case:** Independent AI agent tasks, multi-tenant platform
- **Solution:** Multi-Display (our approach) or Container orchestration
- **Complexity:** Medium (Multi-Display) to High (containers)

---

## 4. Solution: Multiple X11 Displays (Single Container)

Run multiple virtual X servers (Xvfb) on different display numbers within **one container**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Single Docker Container                         │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     FastAPI Backend                          │   │
│  │                    Display Manager                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│  │   Xvfb :1     │  │   Xvfb :2     │  │   Xvfb :3     │   ...    │
│  │   Session 1   │  │   Session 2   │  │   Session 3   │          │
│  │ ┌───────────┐ │  │ ┌───────────┐ │  │ ┌───────────┐ │          │
│  │ │  Firefox  │ │  │ │  Firefox  │ │  │ │  Firefox  │ │          │
│  │ └───────────┘ │  │ └───────────┘ │  │ └───────────┘ │          │
│  │   x11vnc     │  │   x11vnc     │  │   x11vnc     │          │
│  │   :5901      │  │   :5902      │  │   :5903      │          │
│  └───────────────┘  └───────────────┘  └───────────────┘          │
│                                                                      │
│  Shared: Filesystem, Memory, CPU, Network                           │
└─────────────────────────────────────────────────────────────────────┘
```

#### Resource Comparison

| Metric | Per-Container (Approach 1) | Multi-Display (Approach 2) |
|--------|---------------------------|---------------------------|
| **RAM per session** | 500MB - 2GB | 50MB - 200MB |
| **Startup time** | 10-30 seconds | 1-3 seconds |
| **Disk per session** | ~1GB (image layers) | ~0 (shared) |
| **Max sessions** | ~10-20 per host | ~50-100 per host |
| **Docker socket** | Required | Not required |

#### Implementation

```python
# app/services/display_manager.py

import subprocess
import os
from typing import Dict, Optional
import asyncio

class DisplayManager:
    """
    Manages multiple X11 virtual displays within a single container.
    Much lighter than spawning containers - just processes.
    """
    
    def __init__(self):
        self.displays: Dict[str, dict] = {}  # session_id -> display info
        self.next_display = 1
        self.base_vnc_port = 5900
        
    async def create_display(self, session_id: str) -> dict:
        """
        Create a new virtual X11 display for a session.
        Returns display number and VNC port.
        """
        display_num = self.next_display
        self.next_display += 1
        vnc_port = self.base_vnc_port + display_num
        
        # Start Xvfb (virtual framebuffer)
        xvfb_proc = subprocess.Popen([
            "Xvfb", f":{display_num}",
            "-screen", "0", "1920x1080x24",
            "-ac",  # Disable access control
        ])
        
        # Wait for X server to start
        await asyncio.sleep(0.5)
        
        # Start x11vnc for this display
        vnc_proc = subprocess.Popen([
            "x11vnc",
            "-display", f":{display_num}",
            "-rfbport", str(vnc_port),
            "-forever",  # Don't exit after first client disconnects
            "-shared",   # Allow multiple VNC clients
            "-nopw",     # No password (use auth at API level)
        ])
        
        # Start window manager for this display
        wm_proc = subprocess.Popen(
            ["mutter"],  # or openbox, fluxbox, etc.
            env={**os.environ, "DISPLAY": f":{display_num}"}
        )
        
        self.displays[session_id] = {
            "display_num": display_num,
            "vnc_port": vnc_port,
            "xvfb_pid": xvfb_proc.pid,
            "vnc_pid": vnc_proc.pid,
            "wm_pid": wm_proc.pid,
        }
        
        return {
            "display": f":{display_num}",
            "vnc_port": vnc_port,
            "status": "created",
        }
    
    async def destroy_display(self, session_id: str) -> bool:
        """Stop all processes for a display and clean up."""
        if session_id not in self.displays:
            return False
            
        info = self.displays[session_id]
        
        # Kill processes in reverse order
        for pid_key in ["wm_pid", "vnc_pid", "xvfb_pid"]:
            try:
                os.kill(info[pid_key], 9)
            except ProcessLookupError:
                pass
        
        del self.displays[session_id]
        return True
    
    def get_display_env(self, session_id: str) -> Optional[dict]:
        """Get environment variables for running agent in this display."""
        if session_id not in self.displays:
            return None
        
        display_num = self.displays[session_id]["display_num"]
        return {
            "DISPLAY": f":{display_num}",
        }
```

#### Agent Integration

```python
# When running agent for a session, set DISPLAY environment
async def run_agent_for_session(session_id: str, message: str):
    display_env = display_manager.get_display_env(session_id)
    
    # Agent tools (screenshot, click) will use this display
    env = {**os.environ, **display_env}
    
    # The agent's screenshot tool captures from DISPLAY=:N
    # The agent's click/type tools interact with DISPLAY=:N
    # Each session is isolated at the X11 level
```

#### Pros
- ✅ **Much faster** session creation (1-3 seconds vs 10-30)
- ✅ **Much lighter** resource usage (~100MB vs ~1GB per session)
- ✅ **Simpler** - no Docker socket, no container orchestration
- ✅ **Single container** - easier deployment, Render.com compatible!
- ✅ Each session has **isolated visual state** (different X displays)

#### Cons
- ❌ **Shared filesystem** - sessions can see each other's files
- ❌ **Less isolation** - malicious agent could affect other sessions
- ❌ **Process management** - must track and cleanup PIDs carefully
- ❌ **Single point of failure** - container crash loses all sessions
- ❌ **No resource limits** per session (unless using cgroups manually)

#### When to Use Each Approach

| Scenario | Recommended |
|----------|-------------|
| Demo / POC / Homework | ✅ **Multi-Display** |
| Single-tenant deployment | ✅ **Multi-Display** |
| Render.com / simple cloud | ✅ **Multi-Display** |
| Multi-tenant / untrusted users | Container Orchestration |
| Production with SLAs | Container Orchestration |
| Resource-constrained environment | ✅ **Multi-Display** |
| High session count (50+) | ✅ **Multi-Display** |
| Need strong isolation | Consider Container Orchestration (separate doc) |

---

## 5. Implementation Details

**For this project:** Implement **Approach 2 (Multi-Display Single Container)** - it's lighter, simpler, and Render.com compatible.

### Why Multi-Display?

| Concern | Answer |
|---------|--------|
| "How much RAM per session?" | ~100MB (vs ~1GB for containers) |
| "How fast is session creation?" | 1-3 seconds (vs 10-30 for containers) |
| "Does it work on Render.com?" | ✅ Yes! No Docker socket needed |
| "Does it solve the state problem?" | ✅ Yes - each session has isolated X11 display |
| "Is it simpler?" | ✅ Yes - just process management, no orchestration |

### User Experience

```bash
# Developer starts the system
$ docker-compose up

# Single container starts with FastAPI + Display Manager
# No displays created yet

# User creates a session via API
POST /api/v1/sessions
→ DisplayManager starts Xvfb :1 + x11vnc on port 5901
→ Returns session_id with VNC URL (port 5901)

# User sends a message
POST /api/v1/sessions/{id}/messages
→ Agent runs with DISPLAY=:1
→ Screenshots/clicks happen on display :1
→ SSE stream returns results

# Another user creates a session
POST /api/v1/sessions  
→ DisplayManager starts Xvfb :2 + x11vnc on port 5902
→ Completely independent from display :1

# First user returns later
GET /api/v1/sessions/{id}
→ Display :1 still running with their Firefox state
→ They continue exactly where they left off
```

### Implementation Tiers

| Tier | Scope | Description |
|------|-------|-------------|
| **Tier 1** | MVP | Single container, single session (current) ✅ |
| **Tier 2** | Multi-Session | Single container + Multi-Display ⭐ **NEW** |
| **Tier 3** | Production Scale | Container Orchestration (if needed) |

### Future Scaling (If Needed)

If you later need **strong isolation** (untrusted multi-tenant, per-session resource limits), consider:
- Container orchestration with Docker socket
- Kubernetes with per-pod workers

But for this project, Multi-Display is the right choice.

---

## 6. Implementation Plan

### 7.1 Changes Required

To upgrade from single-session to multi-session:

```
Current:                          Multi-Session:
┌─────────────────────┐          ┌─────────────────────┐
│ Single X11 Display  │    →     │ Display Manager     │
│ (hardcoded :1)      │          │ (dynamic :1, :2...) │
└─────────────────────┘          └─────────────────────┘

┌─────────────────────┐          ┌─────────────────────┐
│ Single VNC Server   │    →     │ VNC per Display     │
│ (port 5900)         │          │ (ports 5901, 5902)  │
└─────────────────────┘          └─────────────────────┘

┌─────────────────────┐          ┌─────────────────────┐
│ Agent uses DISPLAY  │    →     │ Agent uses session's│
│ from env (global)   │          │ assigned DISPLAY    │
└─────────────────────┘          └─────────────────────┘
```

### 7.2 Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `app/services/display_manager.py` | **Create** | Manages Xvfb/VNC processes |
| `app/services/session_manager.py` | **Modify** | Use DisplayManager for sessions |
| `app/api/routes/sessions.py` | **Modify** | Return VNC port in response |
| `docker/entrypoint.sh` | **Modify** | Don't start X11/VNC on boot |
| `frontend/js/app.js` | **Modify** | Connect to session-specific VNC |

### 7.3 Estimated Effort

| Task | Time |
|------|------|
| DisplayManager service | 2-3 hours |
| Session API integration | 1-2 hours |
| Frontend VNC routing | 1 hour |
| Testing | 2 hours |
| **Total** | **6-8 hours** |

---

## 7. Future: Multi-Agent Collaboration

The Multi-Display architecture also enables **multiple agents on the same display**:

```
┌─────────────────────────────────┐
│      Shared Display (:1)        │
│   [Browser] [Terminal] [Files]  │
└─────────────────────────────────┘
       ▲           ▲
       │           │
   Agent A      Agent B
   (Research)   (Coding)
```

**Why it works:** X11 supports multiple clients. Screenshot/click/type tools just target a DISPLAY.

**Challenge:** Coordination. Without it, agents step on each other.

**Solutions (in order of complexity):**
1. **Turn-based** - Agents take turns (simplest)
2. **Lock-based** - Acquire control before acting
3. **Orchestrator** - Coordinator assigns tasks

This is **not in scope** for the current implementation, but the architecture supports it.

---

## 8. References

### Projects
- [Anthropic Computer Use Demo](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo)

### Documentation
- [Xvfb Manual](https://www.x.org/releases/X11R7.6/doc/man/man1/Xvfb.1.xhtml)
- [x11vnc Documentation](https://github.com/LibVNC/x11vnc)

---

*This document focuses on the Multi-Display approach. Container orchestration is a future consideration for production multi-tenant deployments.*
