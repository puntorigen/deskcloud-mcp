# Known Limitations

**Author:** Pablo Schaffner  
**Last Updated:** December 2025

This document outlines the current architectural limitations of the computer-use-backend implementation.

---

## 1. Single Desktop Environment

### Limitation

The current implementation uses **one X11 display** (`:1`) shared by all sessions. Only one session can actively use the desktop at a time.

### Impact

| Scenario | Result |
|----------|--------|
| User A creates session, works on task | ✅ Works |
| User B creates session while A is active | ⚠️ Overwrites A's desktop state |
| User A returns to continue | ❌ Desktop state is lost |

### What IS Preserved

- ✅ Session metadata
- ✅ Chat history (all messages)
- ✅ Tool use history

### What is NOT Preserved

- ❌ Browser state (tabs, cookies, forms)
- ❌ Open applications
- ❌ Files created during session
- ❌ Desktop layout

### Future Resolution

Multi-Display architecture using multiple Xvfb instances per session (not yet implemented).

---

## 2. No Session Suspension

### Limitation

Active sessions consume resources (~100-200MB RAM) continuously. There is no way to suspend an inactive session and restore it later.

### Impact

- High memory usage with many idle sessions
- Cannot scale to many concurrent users
- No "hibernate and resume" capability

### Future Resolution

CRIU-based checkpointing for session suspension and restoration (not yet implemented).

---

## 3. Single Container Architecture

### Limitation

Everything runs in one Docker container. A crash or restart loses all active sessions.

### Impact

- Single point of failure
- Cannot scale horizontally
- Updates require restarting all sessions

### Mitigation

- Database persists chat history across restarts
- Multi-Display architecture (see limitation #1) provides session isolation within the container

---

## 4. Shared Filesystem

### Limitation

All sessions share the same filesystem. Files created by one session are visible to all others.

### Impact

- No file isolation between sessions
- Potential data leakage between users
- Disk space shared across all sessions

### Workaround

Future enhancement: Per-session home directories with UID mapping.

---

## 5. No Resource Limits Per Session

### Limitation

Individual sessions cannot have CPU/memory limits. One runaway session can affect others.

### Impact

- A memory-hungry browser tab affects all sessions
- No fair resource allocation
- Cannot guarantee QoS per session

### Workaround

Future enhancement: cgroups-based per-session resource limits.

---

## 6. VNC Streaming Only

### Limitation

Desktop streaming uses VNC (noVNC). WebRTC would provide smoother video.

### Impact

- Higher bandwidth usage
- Some latency in visual feedback
- No audio support

### Status

VNC is adequate for AI agent use cases. WebRTC upgrade is possible but not prioritized.

---

## 7. No Multi-Agent Coordination

### Limitation

While multiple agents *can* target the same display, there's no built-in coordination mechanism.

### Impact

- Agents may interfere with each other
- No turn-taking or locking
- Undefined behavior with concurrent agent actions

### Future Resolution

Multi-agent collaboration with coordination mechanisms (not yet implemented).

---

## 8. Single API Provider Active

### Limitation

While multiple providers are supported (Anthropic, Bedrock, Vertex), only one provider can be configured at a time per deployment.

### Impact

- Cannot dynamically switch providers
- Cannot use different providers for different sessions

### Status

By design - matches upstream Anthropic demo behavior.

---

## Summary Table

| Limitation | Severity | Status |
|------------|----------|--------|
| Single Desktop | High | Future: Multi-display architecture |
| No Session Suspension | Medium | Future: CRIU checkpointing |
| Single Container | Medium | Future: Container orchestration |
| Shared Filesystem | Low | Future: Per-session directories |
| No Resource Limits | Low | Future: cgroups integration |
| VNC Only | Low | Future: WebRTC upgrade |
| No Multi-Agent Coordination | Low | Future: Coordination mechanisms |
| Single Provider | Low | By design |

