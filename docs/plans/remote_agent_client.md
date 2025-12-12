# DeskCloud Remote Agent Client Plan

> ⚠️ **Start Here**: Read [`MASTER_ROADMAP.md`](./MASTER_ROADMAP.md) first for project context and overview.

> **Product Name**: DeskCloud Connect / DeskCloud Agent  
> **Category**: Premium Feature  
> **Target**: Pro, Team, Enterprise tiers  
> **Created**: December 2025  
> **Priority**: 🔴 High - Implement after Dashboard (Phase 6-7)

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Strategic Rationale](#strategic-rationale)
3. [Architecture Overview](#architecture-overview)
4. [Security Model](#security-model)
5. [Client Agent Design](#client-agent-design)
6. [Server Infrastructure](#server-infrastructure)
7. [Protocol Specification](#protocol-specification)
8. [User Experience](#user-experience)
9. [Business Model](#business-model)
10. [Competitive Analysis](#competitive-analysis)
11. [Risk Analysis](#risk-analysis)
12. [Implementation Roadmap](#implementation-roadmap)
13. [Success Metrics](#success-metrics)
14. [Related Plans](#related-plans)

---

## Executive Summary

### Vision

**DeskCloud Connect** is a lightweight client application that users install on their own computers (Windows, macOS, Linux), enabling AI agents to control those machines remotely through the DeskCloud MCP server. This inverts our infrastructure model—instead of hosting virtual machines, users bring their own hardware.

### Key Value Propositions

| Benefit | Description |
|---------|-------------|
| **Any OS** | Support Windows, macOS, and Linux without emulation |
| **Real Hardware** | Access to GPU, USB devices, printers, native apps |
| **Zero Compute Cost** | User's hardware = no VM costs for DeskCloud |
| **Corporate Apps** | Automate Outlook, SAP, Salesforce, internal tools |
| **Native Performance** | No emulation overhead |

### Target Use Cases

1. **Enterprise RPA**: Automate legacy Windows apps (SAP, Salesforce, internal tools)
2. **Personal Automation**: Let AI manage your email, calendar, file organization
3. **Development**: Test across real OS environments
4. **Remote Work**: AI assistant on your work computer from anywhere
5. **Tech Support**: AI-assisted troubleshooting with consent
6. **Server Automation**: 24/7 AI access to headless servers (use "Always" consent mode)
7. **Home Lab**: Control Raspberry Pi, NAS, home servers with AI

### Comparison to Current Offering

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DeskCloud Product Matrix                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐         ┌─────────────────────────┐           │
│  │  DeskCloud Cloud VMs    │         │  DeskCloud Connect      │           │
│  │  (Current)              │         │  (This Plan)            │           │
│  ├─────────────────────────┤         ├─────────────────────────┤           │
│  │ ✓ Ubuntu Linux          │         │ ✓ Windows               │           │
│  │ ✓ Raspberry Pi          │         │ ✓ macOS                 │           │
│  │ ✓ Android (future)      │         │ ✓ Linux                 │           │
│  │                         │         │                         │           │
│  │ • Isolated sandbox      │         │ • User's real computer  │           │
│  │ • We host & pay compute │         │ • User's hardware       │           │
│  │ • Guaranteed clean env  │         │ • Access to real apps   │           │
│  │ • No user setup         │         │ • GPU, USB, printers    │           │
│  └─────────────────────────┘         └─────────────────────────┘           │
│                                                                             │
│           Best for: Testing, demos, untrusted automation                    │
│           Best for: Enterprise RPA, personal automation                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Strategic Rationale

### Why Build This?

1. **Market Gap**: No existing MCP-native solution for controlling user's own computers
2. **Cost Efficiency**: Zero compute costs for remote agent sessions
3. **Enterprise Demand**: Companies want to automate internal Windows apps
4. **Differentiation**: Unique offering vs. Scrapybara, E2B (only offer cloud VMs)
5. **Complementary**: Works alongside our VM offering, not replacing it

### Existing Solutions Analysis

| Solution | Type | Limitation |
|----------|------|------------|
| **PyAutoGUI MCP Server** | Local only | No remote access, no team features |
| **RustDesk / TeamViewer** | Remote desktop | Human control, not AI-native |
| **Scrapybara / E2B** | Cloud VMs | Not user's own computer |
| **Anthropic Computer Use** | Local demo | Reference implementation only |

### DeskCloud Connect Differentiators

- **AI-Native**: Built for MCP protocol, not human remote desktop
- **Managed Infrastructure**: Relay servers, device management, team features
- **Security-First**: E2E encryption, session approval, audit logging
- **Cross-Platform**: Single codebase for Windows, macOS, Linux
- **Dashboard Integration**: Manage all devices from deskcloud.app

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DeskCloud Infrastructure                             │
│                         (Render.com / Vercel)                               │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────┐    │
│  │   MCP Server     │  │   Relay Server   │  │   Signaling Server     │    │
│  │   (FastAPI)      │◄►│   (WebSocket)    │◄►│   (Device Registry)    │    │
│  │                  │  │   NAT Traversal  │  │   Authentication       │    │
│  │   • Tool calls   │  │   • TURN relay   │  │   • Device claiming    │    │
│  │   • AI sessions  │  │   • E2E forward  │  │   • Session approval   │    │
│  └──────────────────┘  └──────────────────┘  └────────────────────────┘    │
│            │                    │                        │                  │
└────────────│────────────────────│────────────────────────│──────────────────┘
             │                    │                        │
             ▼                    ▼                        ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │                             Internet                                   │
    │                     (Encrypted WebSocket tunnels)                     │
    └───────────────────────────────────────────────────────────────────────┘
             │                    │                        │
             ▼                    ▼                        ▼
┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐
│  DeskCloud Connect   │ │  DeskCloud Connect   │ │  DeskCloud Connect   │
│  (Windows Agent)     │ │  (macOS Agent)       │ │  (Linux Agent)       │
│                      │ │                      │ │                      │
│  ┌────────────────┐  │ │  ┌────────────────┐  │ │  ┌────────────────┐  │
│  │ System Tray    │  │ │  │ Menu Bar Item  │  │ │  │ System Tray    │  │
│  │ Icon           │  │ │  │                │  │ │  │ Icon           │  │
│  └────────────────┘  │ │  └────────────────┘  │ │  └────────────────┘  │
│                      │ │                      │ │                      │
│  ┌────────────────┐  │ │  ┌────────────────┐  │ │  ┌────────────────┐  │
│  │ Control Engine │  │ │  │ Control Engine │  │ │  │ Control Engine │  │
│  │ • PyAutoGUI    │  │ │  │ • PyAutoGUI    │  │ │  │ • PyAutoGUI    │  │
│  │ • Screenshot   │  │ │  │ • Screenshot   │  │ │  │ • Screenshot   │  │
│  │ • Input sim    │  │ │  │ • Input sim    │  │ │  │ • Input sim    │  │
│  └────────────────┘  │ │  └────────────────┘  │ │  └────────────────┘  │
│                      │ │                      │ │                      │
│  User's Real HW      │ │  User's Real HW      │ │  User's Real HW      │
│  • GPU, USB, etc.    │ │  • GPU, USB, etc.    │ │  • GPU, USB, etc.    │
└──────────────────────┘ └──────────────────────┘ └──────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **MCP Server** | Receives AI tool calls, routes to appropriate device |
| **Signaling Server** | Device registration, authentication, session coordination |
| **Relay Server** | WebSocket tunnel for NAT traversal, message forwarding |
| **Connect Agent** | Executes control commands, captures screenshots |

### Data Flow for AI Control

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AI Control Session Flow                               │
└─────────────────────────────────────────────────────────────────────────────┘

1. AI Agent (Claude)          2. MCP Server              3. User's Computer
   in Cursor/Claude              (deskcloud.app)            (Connect Agent)
        │                             │                           │
        │ ─────── screenshot ─────────►                           │
        │                             │ ──── screenshot_req ──────►
        │                             │ ◄──── encrypted(png) ─────│
        │ ◄────── base64 image ───────│                           │
        │                             │                           │
        │ ─── click(500, 300) ────────►                           │
        │                             │ ── click_cmd(500,300) ────►
        │                             │              │             │
        │                             │              ▼             │
        │                             │         [Real Click       │
        │                             │          on Screen]       │
        │                             │ ◄────── ack ──────────────│
        │ ◄─────── success ───────────│                           │
        │                             │                           │
        │ ─── type("hello") ──────────►                           │
        │                             │ ──── type_cmd("hello") ───►
        │                             │              │             │
        │                             │              ▼             │
        │                             │         [Real Keystrokes  │
        │                             │          on Keyboard]     │
        │ ◄─────── success ───────────│                           │
```

---

## Security Model

### Security Principles

1. **User Consent**: User must explicitly approve each AI session
2. **Device Ownership**: Only the account that claimed the device can control it
3. **End-to-End Encryption**: DeskCloud relay cannot see command/screenshot content
4. **Minimal Trust**: Agent trusts only cryptographically verified servers
5. **User Control**: Kill switch, timeouts, and restrictions always available

### Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Security Layers                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 1: Device Claiming                                             │   │
│  │ • Agent downloads contain embedded claim token                       │   │
│  │ • Token tied to DeskCloud account                                    │   │
│  │ • Device registered with public key                                  │   │
│  │ • Only claiming account can start sessions                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 2: Session Authorization                                        │   │
│  │ • Before AI control, popup asks user to approve                      │   │
│  │ • Flexible duration: 5 min / 1 hour / 1 day / 7 days / Always       │   │
│  │ • User can revoke at any time via hotkey or UI                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 3: End-to-End Encryption                                        │   │
│  │ • Agent generates Ed25519 keypair on install                         │   │
│  │ • Public key registered with signaling server                        │   │
│  │ • All commands/screenshots encrypted with X25519                     │   │
│  │ • Relay server sees only encrypted blobs                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 4: Action Controls (Optional High-Security Mode)               │   │
│  │ • Restrict AI to specific applications                               │   │
│  │ • Block access to sensitive folders                                  │   │
│  │ • Require confirmation for destructive actions                       │   │
│  │ • Rate limiting on rapid commands                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 5: Audit & Kill Switch                                          │   │
│  │ • Every action logged locally                                        │   │
│  │ • Optional cloud sync for compliance (encrypted)                     │   │
│  │ • Hotkey: Ctrl+Alt+Esc immediately stops session                     │   │
│  │ • Network disconnect = session ends                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Device Claiming Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Device Claiming Flow                                  │
└─────────────────────────────────────────────────────────────────────────────┘

User                    Dashboard                 Signaling            Agent
 │                      (web)                     Server               (local)
 │                         │                         │                    │
 │──Login to dashboard─────►                         │                    │
 │                         │                         │                    │
 │──Click "Add Device"─────►                         │                    │
 │                         │──Generate claim token───►                    │
 │                         │◄──token + download URL──│                    │
 │◄──Download installer────│                         │                    │
 │   (embedded token)      │                         │                    │
 │                         │                         │                    │
 │──Run installer──────────────────────────────────────────────────────────►
 │                         │                         │                    │
 │                         │                         │◄─register(token,   │
 │                         │                         │   device_id,       │
 │                         │                         │   public_key)      │
 │                         │                         │                    │
 │                         │                         │──verify_token──────►
 │                         │                         │◄─valid─────────────│
 │                         │                         │                    │
 │                         │◄─device_claimed─────────│                    │
 │◄─"Device added!"────────│                         │                    │
 │                         │                         │                    │
 │                         │                         │◄═══Heartbeat═══════│
 │                         │                         │    (status,        │
 │                         │                         │     online/offline)│
```

### Session Approval Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Session Approval Popup                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         🔒 DeskCloud Connect                         │   │
│  │                                                                      │   │
│  │     An AI agent is requesting control of this computer.             │   │
│  │                                                                      │   │
│  │     ┌──────────────────────────────────────────────────────────┐   │   │
│  │     │  Requester: your-email@example.com                        │   │   │
│  │     │  Session:   "Help organize my Downloads folder"           │   │   │
│  │     │  Time:      December 10, 2025 at 2:45 PM                  │   │   │
│  │     └──────────────────────────────────────────────────────────┘   │   │
│  │                                                                      │   │
│  │     Allow AI control for:                                           │   │
│  │                                                                      │   │
│  │     ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │   │
│  │     │ 5 min  │  │ 1 hour │  │ 1 day  │  │ 7 days │  │ Always │   │   │
│  │     └────────┘  └────────┘  └────────┘  └────────┘  └────────┘   │   │
│  │                                                                      │   │
│  │     ☐ Remember this choice (don't ask again)                        │   │
│  │                                                                      │   │
│  │                        ┌──────────────┐                             │   │
│  │                        │    Deny      │                             │   │
│  │                        └──────────────┘                             │   │
│  │                                                                      │   │
│  │     💡 "Always" is ideal for servers. Revoke anytime from tray.    │   │
│  │     ⚠️ Press Ctrl+Alt+Esc at any time to stop the session          │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Server Mode (Always-On Access)

For servers and always-on machines, users can grant persistent AI access without approval popups:

**Use Cases for "Always" Access:**
- **Headless servers** - No one at the screen to approve
- **Home lab devices** - Raspberry Pi, NAS, always-on desktops
- **CI/CD runners** - Automated testing machines
- **Kiosk machines** - Unattended systems
- **Development VMs** - VirtualBox/VMware guests

**How It Works:**

1. User approves with "Always" + "Remember this choice"
2. Agent stores approval persistently (encrypted in local config)
3. Future session requests auto-approve without popup
4. User can revoke anytime from:
   - System tray menu → "Revoke Always Access"
   - Dashboard → Device settings → "Revoke persistent access"
   - Emergency: Delete config file or uninstall agent

**Security Safeguards for Always-On:**

| Safeguard | Description |
|-----------|-------------|
| **Account-locked** | Only sessions from the claiming account auto-approve |
| **Audit logging** | All auto-approved sessions logged with timestamp |
| **Heartbeat check** | Agent must be online; offline = no sessions |
| **Dashboard visibility** | "Always-on" devices clearly marked in dashboard |
| **Easy revocation** | One-click revoke from tray or dashboard |

**Agent Config for Always-On:**

```toml
# ~/.config/deskcloud-connect/config.toml

[device]
id = "dev_a1b2c3d4"
claimed_by = "user_xyz123"

[consent]
mode = "always"  # "prompt" | "always"
approved_at = "2025-12-10T14:30:00Z"
approved_until = null  # null = forever, or ISO date
remember_choice = true

[security]
auto_approve_only_for_account = true
require_encryption = true
```

---

## Client Agent Design

### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Language** | Python 3.11+ | Cross-platform, PyAutoGUI ecosystem |
| **GUI** | pystray + tkinter | Lightweight system tray |
| **Screen Capture** | mss | Fast, cross-platform screenshots |
| **Input Control** | PyAutoGUI | Mouse/keyboard automation |
| **Networking** | websockets | Async WebSocket client |
| **Encryption** | cryptography + PyNaCl | E2E with X25519/Ed25519 |
| **Packaging** | PyInstaller | Single executable per OS |
| **Config** | appdirs + TOML | OS-appropriate config paths |

### Agent Package Structure

```
deskcloud-connect/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── agent.py                # Main agent class
│   │
│   ├── control/
│   │   ├── __init__.py
│   │   ├── screen.py           # Screenshot capture (mss)
│   │   ├── mouse.py            # Mouse control (PyAutoGUI)
│   │   ├── keyboard.py         # Keyboard control (PyAutoGUI)
│   │   └── window.py           # Window management
│   │
│   ├── network/
│   │   ├── __init__.py
│   │   ├── signaling.py        # Signaling server connection
│   │   ├── relay.py            # Relay tunnel connection
│   │   └── protocol.py         # JSON-RPC message handling
│   │
│   ├── security/
│   │   ├── __init__.py
│   │   ├── crypto.py           # E2E encryption
│   │   ├── keystore.py         # Secure key storage
│   │   └── consent.py          # Session approval UI
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── tray.py             # System tray icon
│   │   ├── popup.py            # Approval popup
│   │   └── settings.py         # Settings window
│   │
│   └── config/
│       ├── __init__.py
│       └── settings.py         # Configuration management
│
├── assets/
│   ├── icon.ico                # Windows icon
│   ├── icon.icns               # macOS icon
│   └── icon.png                # Linux icon
│
├── installer/
│   ├── windows/
│   │   └── installer.nsi       # NSIS installer script
│   ├── macos/
│   │   └── build_dmg.sh        # DMG builder
│   └── linux/
│       ├── deskcloud.desktop   # Desktop entry
│       └── build_appimage.sh   # AppImage builder
│
├── pyproject.toml
├── requirements.txt
└── README.md
```

### Core Agent Class

```python
# src/agent.py
import asyncio
from dataclasses import dataclass
from typing import Optional
import logging

from .control.screen import ScreenCapture
from .control.mouse import MouseController
from .control.keyboard import KeyboardController
from .network.signaling import SignalingClient
from .network.relay import RelayTunnel
from .security.crypto import E2ECrypto
from .security.consent import ConsentManager
from .ui.tray import SystemTray

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    device_id: str
    signaling_url: str = "wss://signal.deskcloud.app"
    relay_url: str = "wss://relay.deskcloud.app"
    heartbeat_interval: int = 30  # seconds

class DeskCloudAgent:
    """Main agent class that coordinates all components."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.running = False
        self.active_session: Optional[str] = None
        
        # Components
        self.screen = ScreenCapture()
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.crypto = E2ECrypto()
        self.signaling = SignalingClient(config.signaling_url)
        self.relay: Optional[RelayTunnel] = None
        self.consent = ConsentManager()
        self.tray = SystemTray(self)
    
    async def start(self):
        """Start the agent."""
        self.running = True
        logger.info(f"Starting DeskCloud Connect agent: {self.config.device_id}")
        
        # Load or generate keypair
        await self.crypto.initialize()
        
        # Connect to signaling server
        await self.signaling.connect(
            device_id=self.config.device_id,
            public_key=self.crypto.public_key
        )
        
        # Register for session requests
        self.signaling.on_session_request = self._handle_session_request
        
        # Start UI
        self.tray.start()
        
        # Keep running
        while self.running:
            await asyncio.sleep(1)
    
    async def _handle_session_request(self, request: dict):
        """Handle incoming session request from signaling server."""
        logger.info(f"Session request from: {request['requester']}")
        
        # Show consent popup
        approved, duration = await self.consent.request_approval(
            requester=request['requester'],
            description=request.get('description', 'AI control session')
        )
        
        if not approved:
            await self.signaling.reject_session(request['session_id'])
            return
        
        # Start session
        await self._start_session(request, duration)
    
    async def _start_session(self, request: dict, duration_minutes: int):
        """Start an AI control session."""
        session_id = request['session_id']
        self.active_session = session_id
        
        # Establish relay connection
        self.relay = RelayTunnel(
            self.config.relay_url,
            session_id,
            self.crypto
        )
        await self.relay.connect()
        
        # Handle commands
        self.relay.on_command = self._handle_command
        
        # Set timeout
        asyncio.create_task(self._session_timeout(duration_minutes * 60))
        
        logger.info(f"Session started: {session_id} for {duration_minutes} minutes")
        self.tray.set_active_session(True)
    
    async def _handle_command(self, command: dict) -> dict:
        """Handle a control command from the AI."""
        method = command.get('method')
        params = command.get('params', {})
        
        try:
            if method == 'screenshot':
                image = await self.screen.capture()
                return {'image': image, 'width': self.screen.width, 'height': self.screen.height}
            
            elif method == 'mouse_move':
                await self.mouse.move(params['x'], params['y'])
                return {'success': True}
            
            elif method == 'click':
                await self.mouse.click(
                    params.get('x'),
                    params.get('y'),
                    button=params.get('button', 'left')
                )
                return {'success': True}
            
            elif method == 'type':
                await self.keyboard.type_text(params['text'])
                return {'success': True}
            
            elif method == 'key':
                await self.keyboard.press_key(params['key'])
                return {'success': True}
            
            elif method == 'scroll':
                await self.mouse.scroll(
                    params.get('x', 0),
                    params.get('y', 0),
                    clicks=params.get('clicks', 1)
                )
                return {'success': True}
            
            else:
                return {'error': f'Unknown method: {method}'}
                
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return {'error': str(e)}
    
    async def _session_timeout(self, seconds: int):
        """End session after timeout."""
        await asyncio.sleep(seconds)
        if self.active_session:
            await self.end_session("timeout")
    
    async def end_session(self, reason: str = "user"):
        """End the current session."""
        if self.relay:
            await self.relay.close()
            self.relay = None
        
        if self.active_session:
            await self.signaling.end_session(self.active_session, reason)
            self.active_session = None
        
        self.tray.set_active_session(False)
        logger.info(f"Session ended: {reason}")
    
    def kill_switch(self):
        """Emergency stop - called by hotkey."""
        asyncio.create_task(self.end_session("kill_switch"))
        logger.warning("Kill switch activated!")
    
    async def stop(self):
        """Stop the agent."""
        self.running = False
        await self.end_session("shutdown")
        await self.signaling.disconnect()
        self.tray.stop()
```

### Screen Capture Module

```python
# src/control/screen.py
import base64
import io
from typing import Optional, Tuple
import mss
from PIL import Image

class ScreenCapture:
    """High-performance screen capture using mss."""
    
    def __init__(self):
        self.sct = mss.mss()
        self._monitor = self.sct.monitors[1]  # Primary monitor
    
    @property
    def width(self) -> int:
        return self._monitor['width']
    
    @property
    def height(self) -> int:
        return self._monitor['height']
    
    async def capture(
        self,
        quality: int = 85,
        max_size: Optional[Tuple[int, int]] = None
    ) -> str:
        """
        Capture screenshot and return as base64 JPEG.
        
        Args:
            quality: JPEG quality (1-100)
            max_size: Optional (width, height) to resize
        
        Returns:
            Base64 encoded JPEG image
        """
        # Capture screen
        screenshot = self.sct.grab(self._monitor)
        
        # Convert to PIL Image
        img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
        
        # Resize if needed (for bandwidth savings)
        if max_size:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert to JPEG
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality)
        
        # Base64 encode
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def get_display_info(self) -> dict:
        """Get information about all displays."""
        return {
            'monitors': [
                {
                    'index': i,
                    'width': m['width'],
                    'height': m['height'],
                    'left': m['left'],
                    'top': m['top'],
                }
                for i, m in enumerate(self.sct.monitors)
            ]
        }
```

### Consent Popup

```python
# src/security/consent.py
import asyncio
import tkinter as tk
from tkinter import ttk
from typing import Tuple, Optional
import threading

class ConsentManager:
    """Manages session approval popups."""
    
    async def request_approval(
        self,
        requester: str,
        description: str
    ) -> Tuple[bool, int]:
        """
        Show approval popup and wait for user response.
        
        Returns:
            (approved: bool, duration_minutes: int)
        """
        result = {'approved': False, 'duration': 0}
        event = asyncio.Event()
        
        def show_popup():
            root = tk.Tk()
            root.title("DeskCloud Connect")
            root.attributes('-topmost', True)
            root.resizable(False, False)
            
            # Center on screen
            width, height = 450, 320
            x = (root.winfo_screenwidth() - width) // 2
            y = (root.winfo_screenheight() - height) // 2
            root.geometry(f"{width}x{height}+{x}+{y}")
            
            # Main frame
            frame = ttk.Frame(root, padding=20)
            frame.pack(fill=tk.BOTH, expand=True)
            
            # Header
            ttk.Label(
                frame,
                text="🔒 AI Control Request",
                font=('Helvetica', 16, 'bold')
            ).pack(pady=(0, 15))
            
            # Message
            ttk.Label(
                frame,
                text="An AI agent is requesting control of this computer.",
                wraplength=400
            ).pack(pady=(0, 10))
            
            # Details
            details = ttk.LabelFrame(frame, text="Details", padding=10)
            details.pack(fill=tk.X, pady=(0, 15))
            
            ttk.Label(details, text=f"Requester: {requester}").pack(anchor=tk.W)
            ttk.Label(details, text=f"Purpose: {description}").pack(anchor=tk.W)
            
            # Duration selection
            ttk.Label(frame, text="Allow control for:").pack(anchor=tk.W)

            # -1 = "Always" (until revoked)
            duration_var = tk.IntVar(value=60)
            duration_frame = ttk.Frame(frame)
            duration_frame.pack(fill=tk.X, pady=5)

            durations = [
                (5, "5 min"),
                (60, "1 hour"),
                (1440, "1 day"),
                (10080, "7 days"),
                (-1, "Always"),  # -1 = no expiry
            ]
            for mins, label in durations:
                ttk.Radiobutton(
                    duration_frame,
                    text=label,
                    variable=duration_var,
                    value=mins
                ).pack(side=tk.LEFT, padx=5)
            
            # Remember choice checkbox
            remember_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                frame,
                text="Remember this choice (don't ask again)",
                variable=remember_var
            ).pack(anchor=tk.W, pady=5)
            
            ttk.Label(
                frame,
                text="💡 'Always' is ideal for servers. Revoke anytime from system tray.",
                font=('Helvetica', 9),
                foreground='#0D9488'
            ).pack(anchor=tk.W)
            
            # Buttons
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=tk.X, pady=(10, 0))
            
            def approve():
                result['approved'] = True
                result['duration'] = duration_var.get()
                root.destroy()
            
            def deny():
                root.destroy()
            
            ttk.Button(btn_frame, text="Allow", command=approve).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Deny", command=deny).pack(side=tk.LEFT, padx=5)
            
            # Warning
            ttk.Label(
                frame,
                text="⚠️ Press Ctrl+Alt+Esc to stop at any time",
                font=('Helvetica', 9),
                foreground='gray'
            ).pack(pady=(15, 0))
            
            root.mainloop()
            asyncio.get_event_loop().call_soon_threadsafe(event.set)
        
        # Run popup in separate thread
        thread = threading.Thread(target=show_popup)
        thread.start()
        
        # Wait for result
        await event.wait()
        
        return result['approved'], result['duration']
```

---

## Server Infrastructure

### Signaling Server

The signaling server handles device registration, authentication, and session coordination.

```python
# server/signaling/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
from typing import Dict, Optional
import secrets
import asyncio

app = FastAPI(title="DeskCloud Signaling Server")

# In-memory device registry (use Redis in production)
devices: Dict[str, 'DeviceConnection'] = {}
pending_sessions: Dict[str, 'SessionRequest'] = {}

class DeviceConnection:
    def __init__(self, device_id: str, user_id: str, public_key: str, ws: WebSocket):
        self.device_id = device_id
        self.user_id = user_id
        self.public_key = public_key
        self.ws = ws
        self.online = True

class SessionRequest(BaseModel):
    session_id: str
    device_id: str
    requester: str
    description: Optional[str] = None

@app.websocket("/ws/device/{device_id}")
async def device_connection(
    websocket: WebSocket,
    device_id: str,
    token: str  # Claim token or auth token
):
    await websocket.accept()
    
    # Validate token and get user_id
    user_id = await validate_device_token(token, device_id)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    # Receive registration message with public key
    reg_msg = await websocket.receive_json()
    public_key = reg_msg.get('public_key')
    
    # Register device
    device = DeviceConnection(device_id, user_id, public_key, websocket)
    devices[device_id] = device
    
    try:
        while True:
            # Handle heartbeat and messages
            msg = await websocket.receive_json()
            
            if msg['type'] == 'ping':
                await websocket.send_json({'type': 'pong'})
            
            elif msg['type'] == 'session_response':
                session_id = msg['session_id']
                if session_id in pending_sessions:
                    # Forward response to MCP server
                    await notify_session_response(session_id, msg)
            
    except WebSocketDisconnect:
        devices[device_id].online = False
        del devices[device_id]

@app.post("/api/v1/sessions/request")
async def request_session(request: SessionRequest, user_id: str = Depends(get_current_user)):
    """Request an AI control session on a device."""
    device = devices.get(request.device_id)
    
    if not device:
        return {"error": "Device offline"}
    
    if device.user_id != user_id:
        return {"error": "Not your device"}
    
    # Generate session ID
    session_id = secrets.token_urlsafe(16)
    
    # Store pending session
    pending_sessions[session_id] = request
    
    # Send request to device
    await device.ws.send_json({
        'type': 'session_request',
        'session_id': session_id,
        'requester': request.requester,
        'description': request.description
    })
    
    return {"session_id": session_id, "status": "pending"}
```

### Relay Server

The relay server provides WebSocket tunneling for NAT traversal.

```python
# server/relay/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict
import asyncio

app = FastAPI(title="DeskCloud Relay Server")

# Active session tunnels
sessions: Dict[str, 'SessionTunnel'] = {}

class SessionTunnel:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.agent_ws: Optional[WebSocket] = None
        self.mcp_ws: Optional[WebSocket] = None
        self.message_queue = asyncio.Queue()
    
    async def forward_to_agent(self, message: bytes):
        if self.agent_ws:
            await self.agent_ws.send_bytes(message)
    
    async def forward_to_mcp(self, message: bytes):
        if self.mcp_ws:
            await self.mcp_ws.send_bytes(message)

@app.websocket("/ws/session/{session_id}/agent")
async def agent_tunnel(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for Connect agent."""
    await websocket.accept()
    
    tunnel = sessions.get(session_id) or SessionTunnel(session_id)
    tunnel.agent_ws = websocket
    sessions[session_id] = tunnel
    
    try:
        while True:
            # Receive encrypted message from agent
            message = await websocket.receive_bytes()
            # Forward to MCP server
            await tunnel.forward_to_mcp(message)
    except WebSocketDisconnect:
        tunnel.agent_ws = None

@app.websocket("/ws/session/{session_id}/mcp")
async def mcp_tunnel(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for MCP server."""
    await websocket.accept()
    
    tunnel = sessions.get(session_id) or SessionTunnel(session_id)
    tunnel.mcp_ws = websocket
    sessions[session_id] = tunnel
    
    try:
        while True:
            # Receive encrypted command from MCP
            message = await websocket.receive_bytes()
            # Forward to agent
            await tunnel.forward_to_agent(message)
    except WebSocketDisconnect:
        tunnel.mcp_ws = None
```

### MCP Server Integration

Extend the existing MCP server to support remote agents:

```python
# app/services/remote_agent_backend.py
from abc import ABC
from typing import Optional
import aiohttp
from dataclasses import dataclass

from app.services.display_manager import DisplayBackend, DisplayInfo

@dataclass
class RemoteDeviceInfo:
    device_id: str
    device_name: str
    os_type: str  # windows, macos, linux
    online: bool
    last_seen: str

class RemoteAgentBackend(DisplayBackend):
    """Display backend that connects to user's remote computer."""
    
    def __init__(self, signaling_url: str, relay_url: str):
        self.signaling_url = signaling_url
        self.relay_url = relay_url
        self._sessions: Dict[str, 'RemoteSession'] = {}
    
    @property
    def os_type(self) -> str:
        return "remote"  # Actual OS determined by device
    
    async def list_devices(self, user_id: str) -> list[RemoteDeviceInfo]:
        """List all devices registered to a user."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.signaling_url}/api/v1/devices",
                headers={"Authorization": f"Bearer {user_id}"}
            ) as resp:
                devices = await resp.json()
                return [RemoteDeviceInfo(**d) for d in devices]
    
    async def create_instance(self, session_id: str, config: dict) -> DisplayInfo:
        """Start a remote control session."""
        device_id = config['device_id']
        user_id = config['user_id']
        
        # Request session via signaling server
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.signaling_url}/api/v1/sessions/request",
                json={
                    "device_id": device_id,
                    "requester": user_id,
                    "description": config.get('description', 'AI control session')
                }
            ) as resp:
                result = await resp.json()
        
        if 'error' in result:
            raise Exception(result['error'])
        
        # Wait for user approval (with timeout)
        approved = await self._wait_for_approval(result['session_id'], timeout=60)
        
        if not approved:
            raise Exception("Session not approved by user")
        
        # Connect to relay
        remote_session = await self._connect_relay(session_id, device_id)
        self._sessions[session_id] = remote_session
        
        # Get device info for display dimensions
        device_info = await self._get_device_info(device_id)
        
        return DisplayInfo(
            session_id=session_id,
            os_type=device_info.os_type,
            display_url=f"remote://{device_id}",  # Not VNC, handled differently
            width=device_info.width,
            height=device_info.height,
            is_ready=True
        )
    
    async def get_screenshot(self, session_id: str) -> bytes:
        """Get screenshot from remote device."""
        session = self._sessions.get(session_id)
        if not session:
            raise Exception("Session not found")
        
        return await session.screenshot()
    
    async def execute_action(self, session_id: str, action: dict) -> dict:
        """Execute an action on the remote device."""
        session = self._sessions.get(session_id)
        if not session:
            raise Exception("Session not found")
        
        return await session.execute(action)
    
    async def destroy_instance(self, session_id: str) -> None:
        """End the remote session."""
        session = self._sessions.get(session_id)
        if session:
            await session.close()
            del self._sessions[session_id]
```

---

## Protocol Specification

### Message Format

All messages use JSON-RPC 2.0 format, encrypted with X25519-XSalsa20-Poly1305.

```typescript
// Request
interface Request {
  jsonrpc: "2.0";
  method: string;
  params?: Record<string, any>;
  id: number;
}

// Response
interface Response {
  jsonrpc: "2.0";
  result?: any;
  error?: { code: number; message: string };
  id: number;
}
```

### Control Commands

| Method | Parameters | Description |
|--------|------------|-------------|
| `screenshot` | `quality?: number` | Capture screen |
| `mouse_move` | `x: number, y: number` | Move cursor |
| `click` | `x?: number, y?: number, button?: string` | Click |
| `double_click` | `x?: number, y?: number` | Double click |
| `right_click` | `x?: number, y?: number` | Right click |
| `drag` | `from: {x, y}, to: {x, y}` | Drag and drop |
| `scroll` | `x?: number, y?: number, clicks: number` | Scroll wheel |
| `type` | `text: string` | Type text |
| `key` | `key: string, modifiers?: string[]` | Press key |
| `hotkey` | `keys: string[]` | Key combination |
| `get_cursor` | - | Get cursor position |
| `get_screen_size` | - | Get screen dimensions |

### Example Session

```json
// MCP Server → Agent: Screenshot request
{
  "jsonrpc": "2.0",
  "method": "screenshot",
  "params": {"quality": 80},
  "id": 1
}

// Agent → MCP Server: Screenshot response
{
  "jsonrpc": "2.0",
  "result": {
    "image": "/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "width": 1920,
    "height": 1080
  },
  "id": 1
}

// MCP Server → Agent: Click command
{
  "jsonrpc": "2.0",
  "method": "click",
  "params": {"x": 500, "y": 300, "button": "left"},
  "id": 2
}

// Agent → MCP Server: Click confirmation
{
  "jsonrpc": "2.0",
  "result": {"success": true},
  "id": 2
}
```

---

## User Experience

### Installation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Installation Journey                                  │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: Dashboard                    Step 2: Download
┌─────────────────────────┐         ┌─────────────────────────┐
│  deskcloud.app/devices  │         │  Download started...    │
│                         │         │                         │
│  Your Devices           │   ───►  │  DeskCloud-Connect-     │
│  ──────────────         │         │  Windows-1.0.0.exe      │
│  (none yet)             │         │                         │
│                         │         │  ✓ Includes your        │
│  [+ Add Device]         │         │    account claim token  │
└─────────────────────────┘         └─────────────────────────┘

Step 3: Install                      Step 4: Connected!
┌─────────────────────────┐         ┌─────────────────────────┐
│  ☁️ DeskCloud Connect    │         │  deskcloud.app/devices  │
│                         │         │                         │
│  Installing...          │   ───►  │  Your Devices           │
│  [████████░░░░░] 60%    │         │  ──────────────         │
│                         │         │  🟢 Work Laptop         │
│  ✓ Create tray icon     │         │     Windows 11          │
│  ✓ Register device      │         │     Online              │
│  ○ Complete setup       │         │                         │
└─────────────────────────┘         └─────────────────────────┘
```

### System Tray States

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        System Tray Icon States                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🔵 Normal (Connected, Idle)      🟢 Active Session                        │
│     ┌─────────────────────┐         ┌─────────────────────┐                │
│     │ ☁️ DeskCloud Connect │         │ ☁️ DeskCloud Connect │                │
│     ├─────────────────────┤         ├─────────────────────┤                │
│     │ ✓ Connected         │         │ 🟢 AI Session Active │                │
│     │                     │         │    23:45 remaining   │                │
│     │ ─────────────────── │         │                     │                │
│     │ Settings            │         │ ─────────────────── │                │
│     │ View Logs           │         │ ⬛ End Session       │                │
│     │ ─────────────────── │         │ Settings            │                │
│     │ Quit                │         │ ─────────────────── │                │
│     └─────────────────────┘         │ Quit                │                │
│                                     └─────────────────────┘                │
│                                                                             │
│  🔴 Disconnected                  ⚠️ Session Request                       │
│     ┌─────────────────────┐         ┌─────────────────────┐                │
│     │ ☁️ DeskCloud Connect │         │ ☁️ DeskCloud Connect │                │
│     ├─────────────────────┤         ├─────────────────────┤                │
│     │ ⚠️ Disconnected     │         │ 🔔 Session Request!  │                │
│     │   Reconnecting...   │         │    Click to respond │                │
│     │                     │         │                     │                │
│     │ ─────────────────── │         │ ─────────────────── │                │
│     │ Reconnect Now       │         │ View Request        │                │
│     │ Settings            │         │ Settings            │                │
│     │ ─────────────────── │         │ ─────────────────── │                │
│     │ Quit                │         │ Quit                │                │
│     └─────────────────────┘         └─────────────────────┘                │
│                                                                             │
│  🟣 Always-On Mode (Server)                                                 │
│     ┌─────────────────────┐                                                 │
│     │ ☁️ DeskCloud Connect │                                                 │
│     ├─────────────────────┤                                                 │
│     │ 🟣 Always-On Mode   │                                                 │
│     │   Auto-approving AI │                                                 │
│     │   sessions          │                                                 │
│     │                     │                                                 │
│     │ ─────────────────── │                                                 │
│     │ Revoke Always Access│                                                 │
│     │ View Session Log    │                                                 │
│     │ Settings            │                                                 │
│     │ ─────────────────── │                                                 │
│     │ Quit                │                                                 │
│     └─────────────────────┘                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dashboard Device Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DeskCloud                                             pablo@example.com ▼  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Devices                                              [+ Add Device]        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🟢 Work Laptop                                                      │   │
│  │  ────────────────────────────────────────────────────────────────── │   │
│  │  OS: Windows 11 Pro                   │  Last Active: Just now      │   │
│  │  Device ID: dev_a1b2c3d4              │  Sessions: 47               │   │
│  │                                                                      │   │
│  │  [Start AI Session]  [View History]  [Settings]  [Remove]           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🟣 Home Server                                        [ALWAYS-ON]   │   │
│  │  ────────────────────────────────────────────────────────────────── │   │
│  │  OS: Ubuntu 24.04 LTS                 │  Last Active: Just now      │   │
│  │  Device ID: dev_srv1234               │  Sessions: 847 (auto)       │   │
│  │                                                                      │   │
│  │  [Start AI Session]  [View History]  [Revoke Always]  [Remove]      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🟢 Personal MacBook                                                 │   │
│  │  ────────────────────────────────────────────────────────────────── │   │
│  │  OS: macOS 14.2 Sonoma                │  Last Active: 5 min ago     │   │
│  │  Device ID: dev_e5f6g7h8              │  Sessions: 12               │   │
│  │                                                                      │   │
│  │  [Start AI Session]  [View History]  [Settings]  [Remove]           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🔴 Office Desktop                                                   │   │
│  │  ────────────────────────────────────────────────────────────────── │   │
│  │  OS: Windows 10                       │  Last Active: 3 days ago    │   │
│  │  Device ID: dev_i9j0k1l2              │  Sessions: 8                │   │
│  │                                                                      │   │
│  │  [Offline - Waiting for connection]   [Settings]  [Remove]          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Business Model

### Pricing Strategy

Remote Agent is available on **all paid tiers** - it's cheaper for us to provide (user's hardware), so we include it as a perk for paying customers:

| Tier | Remote Devices | Remote Sessions | Cloud VM Sessions | Price |
|------|----------------|-----------------|-------------------|-------|
| **Free** | ❌ | ❌ | 25/month | $0 |
| **Pro** | 3 | Unlimited | 250/month | $29/mo |
| **Team** | 10 | Unlimited | 1,000/month | $99/mo |
| **Enterprise** | Unlimited | Unlimited | Unlimited | Custom |

> **Why unlimited remote sessions for paid tiers?**
> Remote agent sessions cost us almost nothing (~$0.002 relay bandwidth vs $0.025 cloud VM compute). 
> By making it unlimited on paid plans, we:
> 1. Incentivize upgrades from Free tier
> 2. Encourage heavy usage (stickiness)
> 3. Position as "all-you-can-eat" for servers running 24/7

### Cost Analysis

| Cost Item | Cloud VM (per session) | Remote Agent (per session) |
|-----------|------------------------|---------------------------|
| Compute | ~$0.02 | $0 (user's HW) |
| Bandwidth | ~$0.005 | ~$0.001 |
| Relay server | N/A | ~$0.001 |
| **Total** | ~$0.025 | ~$0.002 |

**90% cost reduction** for remote agent sessions vs. cloud VMs!

### Revenue Opportunities

1. **Higher Margins**: Same pricing, 10x lower costs
2. **Enterprise Upsell**: On-premise relay server ($500/mo)
3. **Compliance Add-ons**: Audit logging, video recording ($10/device/mo)
4. **Team Features**: Shared device pools, RBAC

---

## Competitive Analysis

| Feature | DeskCloud Connect | PyAutoGUI MCP | RustDesk | TeamViewer |
|---------|-------------------|---------------|----------|------------|
| AI-Native (MCP) | ✅ | ✅ | ❌ | ❌ |
| Remote Access | ✅ | ❌ | ✅ | ✅ |
| Team Management | ✅ | ❌ | ⚠️ | ✅ |
| E2E Encryption | ✅ | N/A | ✅ | ✅ |
| Session Approval | ✅ | N/A | ⚠️ | ⚠️ |
| Dashboard | ✅ | ❌ | ⚠️ | ✅ |
| Multi-OS | ✅ | ✅ | ✅ | ✅ |
| Self-Hosted Option | ✅ | N/A | ✅ | ❌ |
| Open Source | Core only | ✅ | ✅ | ❌ |
| Price (Team) | $99/mo | Free | ~$50/mo | ~$150/mo |

### Unique Position

DeskCloud Connect is the **only solution** that combines:
- MCP protocol (AI-native)
- Remote access (not just local)
- Managed infrastructure (not DIY)
- Security-first design (approval flow)
- Dashboard integration (enterprise-ready)

---

## Risk Analysis

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| NAT traversal failures | High | Medium | TURN relay fallback, multiple providers |
| Cross-platform bugs | Medium | High | Extensive testing matrix, beta program |
| Latency issues | Medium | Medium | Adaptive quality, regional relay servers |
| Screenshot bandwidth | Medium | Low | JPEG compression, delta updates |

### Security Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Unauthorized access | Critical | Low | E2E encryption, device claiming, session approval |
| AI damages computer | High | Medium | Clear ToS, optional action confirmation |
| Social engineering | High | Low | Installer requires account, visible tray icon |
| Data exfiltration | High | Low | E2E encryption, no server-side storage |

### Business Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Low adoption | High | Medium | Free tier, easy onboarding |
| Support burden | Medium | Medium | Self-service docs, community forum |
| Competitor copies | Medium | Medium | First-mover advantage, integration depth |

---

## Implementation Roadmap

### Phase 1: Core Agent (Weeks 1-4)

**Week 1-2: Agent Foundation**
- [ ] Python project setup with PyAutoGUI, mss, websockets
- [ ] Basic control engine (screenshot, mouse, keyboard)
- [ ] System tray icon with pystray
- [ ] Configuration management

**Week 3-4: Server Infrastructure**
- [ ] Signaling server (device registration)
- [ ] Simple relay server
- [ ] Database models (Device, RemoteSession)
- [ ] Basic API endpoints

### Phase 2: Security Layer (Weeks 5-7)

**Week 5: Device Claiming**
- [ ] Claim token generation
- [ ] Installer with embedded token
- [ ] Device registration flow

**Week 6: Session Approval**
- [ ] Consent popup UI
- [ ] Session request/response flow
- [ ] Timeout and expiry handling

**Week 7: E2E Encryption**
- [ ] X25519 key exchange
- [ ] XSalsa20-Poly1305 encryption
- [ ] Secure key storage per OS

### Phase 3: Cross-Platform Packaging (Weeks 8-10)

**Week 8: Windows**
- [ ] NSIS or MSI installer
- [ ] Code signing certificate
- [ ] Windows-specific fixes

**Week 9: macOS**
- [ ] App bundle creation
- [ ] DMG packaging
- [ ] Apple notarization

**Week 10: Linux**
- [ ] DEB package
- [ ] RPM package
- [ ] AppImage for universal

### Phase 4: Dashboard Integration (Weeks 11-12)

**Week 11: Device Management**
- [ ] Device list page
- [ ] Device settings page
- [ ] Add device flow

**Week 12: Session Features**
- [ ] Start session from dashboard
- [ ] Session history
- [ ] Remote device selector in MCP

### Phase 5: Polish & Launch (Weeks 13-14)

**Week 13: Testing & Bug Fixes**
- [ ] Cross-platform testing matrix
- [ ] Beta user feedback
- [ ] Performance optimization

**Week 14: Launch**
- [ ] Documentation
- [ ] Marketing materials
- [ ] Public release

### Future Phases

**Phase 6: Enterprise Features**
- On-premise relay server
- SSO/SAML integration
- Compliance audit logging

**Phase 7: Advanced Features**
- Multi-monitor support
- File transfer
- Clipboard sync
- Session recording

---

## Success Metrics

### Adoption Metrics

| Metric | Target (Month 1) | Target (Month 6) |
|--------|------------------|------------------|
| Agent downloads | 500 | 5,000 |
| Active devices | 100 | 1,500 |
| Daily sessions | 50 | 500 |
| Paid conversions | 5% | 15% |

### Quality Metrics

| Metric | Target |
|--------|--------|
| Session success rate | > 95% |
| Avg. screenshot latency | < 500ms |
| NAT traversal success | > 90% |
| Agent crash rate | < 0.1% |

### Business Metrics

| Metric | Target (Year 1) |
|--------|-----------------|
| Remote session revenue | $50K ARR |
| Enterprise customers | 3 |
| Support tickets per 100 users | < 5 |

---

## Related Plans

- [Next.js Landing Page & Dashboard](./nextjs_landing_dashboard.md) - Dashboard integration
- [Session Video Recording](./session_video_recording.md) - Recording remote sessions
- [Multi-OS Support](./multi_os_support.md) - Cloud VM alternatives
- [Custom Image Builder](./custom_image_builder.md) - Custom environments

---

## Appendix A: OS-Specific Considerations

### Windows

```python
# Windows-specific setup
import winreg
import ctypes

def add_to_startup():
    """Add agent to Windows startup."""
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(key, "DeskCloudConnect", 0, winreg.REG_SZ, sys.executable)

def request_admin():
    """Request UAC elevation if needed."""
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
```

### macOS

```python
# macOS-specific setup
import subprocess

def add_to_login_items():
    """Add agent to macOS login items."""
    subprocess.run([
        'osascript', '-e',
        f'tell application "System Events" to make login item at end '
        f'with properties {{path:"{sys.executable}", hidden:true}}'
    ])

def request_accessibility():
    """Request accessibility permissions for input control."""
    # PyAutoGUI will prompt automatically, but we can check
    subprocess.run(['tccutil', 'reset', 'Accessibility', 'com.deskcloud.connect'])
```

### Linux

```python
# Linux-specific setup
import os

def add_to_autostart():
    """Add agent to XDG autostart."""
    desktop_entry = """[Desktop Entry]
Type=Application
Name=DeskCloud Connect
Exec={executable}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
    autostart_dir = os.path.expanduser("~/.config/autostart")
    os.makedirs(autostart_dir, exist_ok=True)
    
    with open(f"{autostart_dir}/deskcloud-connect.desktop", "w") as f:
        f.write(desktop_entry.format(executable=sys.executable))
```

---

## Appendix B: Encryption Details

### Key Exchange

```python
from nacl.public import PrivateKey, Box
from nacl.signing import SigningKey
import base64

class E2ECrypto:
    def __init__(self):
        # Generate identity keypair (Ed25519)
        self.signing_key = SigningKey.generate()
        self.verify_key = self.signing_key.verify_key
        
        # Generate encryption keypair (X25519)
        self.private_key = PrivateKey.generate()
        self.public_key = self.private_key.public_key
    
    def encrypt(self, plaintext: bytes, recipient_public_key: bytes) -> bytes:
        """Encrypt a message for a recipient."""
        box = Box(self.private_key, recipient_public_key)
        return box.encrypt(plaintext)
    
    def decrypt(self, ciphertext: bytes, sender_public_key: bytes) -> bytes:
        """Decrypt a message from a sender."""
        box = Box(self.private_key, sender_public_key)
        return box.decrypt(ciphertext)
    
    @property
    def public_key_base64(self) -> str:
        return base64.b64encode(bytes(self.public_key)).decode()
```

---

## Appendix C: Testing Matrix

| OS | Version | Architecture | Status |
|----|---------|--------------|--------|
| Windows | 10 | x64 | Required |
| Windows | 11 | x64 | Required |
| Windows | 11 | ARM64 | Optional |
| macOS | 12 Monterey | x64 | Required |
| macOS | 13 Ventura | ARM64 | Required |
| macOS | 14 Sonoma | ARM64 | Required |
| Ubuntu | 22.04 LTS | x64 | Required |
| Ubuntu | 24.04 LTS | x64 | Required |
| Fedora | 39+ | x64 | Optional |
| Debian | 12 | x64 | Optional |
