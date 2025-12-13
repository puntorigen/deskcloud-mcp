# Known Limitations

**Author:** Pablo Schaffner  
**Last Updated:** December 2025

This document outlines the current architectural limitations of DeskCloud MCP.

---

## Current Capabilities

Before discussing limitations, here's what **is** supported:

| Feature | Status |
|---------|--------|
| Multi-session support | ✅ Each session gets isolated X11 display |
| Filesystem isolation | ✅ OverlayFS per session (isolated HOME, Downloads, browser profile) |
| Per-session VNC | ✅ Each session has its own VNC/noVNC port |
| Session TTL & cleanup | ✅ Auto-destroy after 1 hour of inactivity |
| Chat history persistence | ✅ SQLite/PostgreSQL |
| BYOK (Bring Your Own Key) | ✅ Users provide their own Anthropic API key |

---

## 1. Anthropic-Only

### Limitation

Currently only supports Claude models via Anthropic's computer use capabilities. Other providers (OpenAI, Google, open source) are not supported.

### Impact

- Requires an Anthropic API key
- Cannot use GPT-4o, Gemini, or other vision+tool-calling models

### Future

The architecture could be extended to support other providers with vision and tool-calling capabilities, but this would require significant refactoring of the agent loop.

---

## 2. No Session Suspension

### Limitation

Active sessions consume resources (~100MB RAM) continuously. There is no way to suspend an inactive session and restore it later.

### Impact

- Memory usage scales linearly with active sessions
- Cannot "hibernate and resume" a session
- Sessions are destroyed after TTL expires

### Future

CRIU-based checkpointing could enable session snapshots and restoration.

---

## 3. Single Container Architecture

### Limitation

All sessions run within one Docker container. A container restart loses all active sessions.

### Impact

- Single point of failure
- Cannot scale horizontally across machines
- Updates require restarting all sessions

### Mitigation

- Database persists chat history across restarts
- Session metadata is preserved; only desktop state is lost

---

## 4. No Per-Session Resource Limits

### Limitation

Individual sessions cannot have CPU/memory limits. One runaway session can affect others.

### Impact

- A memory-hungry browser tab affects all sessions
- No fair resource allocation between sessions
- Cannot guarantee QoS per session

### Future

cgroups-based per-session resource limits could address this.

---

## 5. VNC Streaming Only

### Limitation

Desktop streaming uses VNC (via noVNC). WebRTC would provide smoother video.

### Impact

- Higher bandwidth usage than WebRTC
- Some latency in visual feedback
- No audio support

### Status

VNC is adequate for AI agent use cases where the human is observing, not interacting. WebRTC upgrade is possible but not prioritized.

---

## 6. No Multi-Agent Coordination

### Limitation

Each session is single-agent. There's no built-in mechanism for multiple agents to collaborate on the same desktop.

### Impact

- Cannot have multiple AI agents working together
- No turn-taking or locking mechanisms

### Status

Single-agent per session is the intended design. Multi-agent collaboration would require coordination mechanisms.

---

## 7. Linux Desktop Only

### Limitation

The virtual desktop runs Ubuntu Linux. Windows and macOS are not supported.

### Impact

- Cannot test Windows-specific applications
- Cannot automate macOS workflows

### Future

Windows support would require different virtualization (QEMU/KVM). macOS has licensing restrictions.

---

## Summary Table

| Limitation | Severity | Status |
|------------|----------|--------|
| Anthropic-only | Medium | By design (for now) |
| No session suspension | Medium | Future: CRIU checkpointing |
| Single container | Medium | Future: Container orchestration |
| No per-session limits | Low | Future: cgroups integration |
| VNC only | Low | Adequate for current use |
| No multi-agent | Low | By design |
| Linux only | Low | Future: Windows support |
