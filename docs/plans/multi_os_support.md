# Multi-OS Support Plan

> ⚠️ **Start Here**: Read [`MASTER_ROADMAP.md`](./MASTER_ROADMAP.md) first for project context and overview.

> **DeskCloud Platform Extension**  
> **Status:** Planning  
> **Created:** December 2025  
> **Priority**: 🟡 Medium - Raspberry Pi in Phase 8, Android/Windows deferred

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Strategic Rationale](#strategic-rationale)
3. [Competitive Analysis](#competitive-analysis)
4. [Supported Operating Systems](#supported-operating-systems)
5. [Architecture Overview](#architecture-overview)
6. [Android Support](#android-support)
7. [Windows Support](#windows-support)
8. [Raspberry Pi Support](#raspberry-pi-support)
9. [macOS Considerations](#macos-considerations)
10. [API & Protocol Design](#api--protocol-design)
11. [Pricing Strategy](#pricing-strategy)
12. [Implementation Roadmap](#implementation-roadmap)
13. [Infrastructure Requirements](#infrastructure-requirements)
14. [Risks & Mitigations](#risks--mitigations)
15. [Success Metrics](#success-metrics)
16. [Related Plans](#related-plans)

---

## Executive Summary

### The Problem

DeskCloud currently supports only Ubuntu/Linux desktops. While powerful, **80% of "computer use" tasks could be done with Playwright** (browser automation). The real value of full OS control lies in:

- **Mobile app automation** (Android/iOS)
- **Windows desktop apps** (Excel, SAP, legacy software)
- **IoT/Embedded systems** (Raspberry Pi, hardware)
- **Native application testing** (things browsers can't do)

### The Solution

Extend DeskCloud to support **multiple operating systems**, prioritizing underserved markets:

| OS | Priority | Market Gap | Competition | Effort |
|----|:--------:|------------|-------------|--------|
| **Android** | ⭐ 1st | No AI+BYOK mobile testing | BrowserStack has no AI | Medium |
| **Raspberry Pi** | ⭐ 2nd | Zero competitors | Unique offering! | Low |
| **Windows** | 3rd | Scrapybara already has it | Direct competition | High |
| **macOS** | ❌ | Blocked by Apple licensing | N/A | Very High |

> **Strategy:** Focus on markets where we have NO direct competition, rather than competing head-to-head with Scrapybara on Windows.

### Value Proposition

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser Automation                          │
│  Playwright, Puppeteer, Browserbase, Steel                      │
│  → Crowded market, commoditized                                 │
│  → Free/cheap alternatives exist                                │
└─────────────────────────────────────────────────────────────────┘
                              vs.
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-OS AI Automation                       │
│  DeskCloud with Ubuntu + Raspberry Pi (+ Android/Windows later) │
│  → Unique market position                                       │
│  → BYOK pricing (10x cheaper than alternatives)                 │
│  → Open source core (trust, flexibility)                        │
│  → AI-native (MCP protocol, not legacy scripting)              │
└─────────────────────────────────────────────────────────────────┘
```

### Cost-Efficient Phased Approach

```
┌─────────────────────────────────────────────────────────────────┐
│  NOW: Render.com + Vercel Only (~$70-120/month)                 │
│  ├── Ubuntu/Linux ✅                                            │
│  └── Raspberry Pi ✅ (QEMU, no KVM needed)                      │
├─────────────────────────────────────────────────────────────────┤
│  FUTURE: When Revenue > $500/month                              │
│  ├── + Dedicated Server (~$40-100/month)                        │
│  └── + Android Support                                          │
├─────────────────────────────────────────────────────────────────┤
│  LATER: When Revenue > $1000/month OR Enterprise Demand         │
│  └── + Windows Support                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Strategic Rationale

### What Browsers CAN'T Do

| Capability | Browser/Playwright | Full OS |
|------------|:------------------:|:-------:|
| Web browsing | ✅ | ✅ |
| Native desktop apps (Excel, SAP, Adobe) | ❌ | ✅ |
| Mobile apps (Android/iOS) | ❌ | ✅ |
| System dialogs, file pickers | ❌ | ✅ |
| Hardware access (USB, Bluetooth, GPIO) | ❌ | ✅ |
| Legacy enterprise software | ❌ | ✅ |
| Software installation/configuration | ❌ | ✅ |
| Multi-app workflows | ❌ | ✅ |
| System administration | ❌ | ✅ |

### Market Opportunity

| Segment | Market Size | Current Leaders | AI+BYOK Exists? | DeskCloud Opportunity |
|---------|-------------|-----------------|:---------------:|----------------------|
| Browser automation | Commoditized | Playwright (free) | N/A | Low differentiation |
| **Mobile testing** | $1B+ | BrowserStack ($249/mo) | ❌ NO | **HUGE gap** |
| **IoT/Embedded** | Growing | None | ❌ NO | **Unique offering** |
| Windows RPA | $50B+ | UiPath, Scrapybara | ✅ Yes | Lower priority |

### Strategic Focus: Underserved Markets

```
┌─────────────────────────────────────────────────────────────────┐
│                    MARKET COMPETITION ANALYSIS                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ANDROID MOBILE TESTING                                        │
│   ├── BrowserStack: $249/mo, NO AI, NO BYOK                    │
│   ├── Sauce Labs: $199/mo, NO AI, NO BYOK                      │
│   ├── Scrapybara: ❓ Unknown                                    │
│   └── DeskCloud: AI-native + BYOK = 10x cheaper 🎯              │
│                                                                 │
│   RASPBERRY PI / IoT                                            │
│   ├── Competitors: NONE                                         │
│   └── DeskCloud: First mover advantage 🎯                       │
│                                                                 │
│   WINDOWS                                                       │
│   ├── Scrapybara: Already supports Windows 11                  │
│   ├── UiPath: Enterprise RPA                                   │
│   └── DeskCloud: Direct competition, less differentiation      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Priority Order

1. **Android First** - $1B+ market, no AI+BYOK solution exists
2. **Raspberry Pi Second** - Zero competitors, unique positioning, low effort
3. **Windows Later** - Scrapybara already there, compete after we're established

---

## Competitive Analysis

### Direct Competitors

#### Scrapybara ⚠️ Primary Competitor

| Feature | Scrapybara | DeskCloud (Planned) |
|---------|------------|---------------------|
| **Ubuntu/Linux** | ✅ | ✅ |
| **Windows 11** | ✅ (2x compute cost) | ✅ (planned) |
| **Android** | ❓ Unknown | ✅ (planned) |
| **Raspberry Pi** | ❌ | ✅ (planned) |
| **BYOK Model** | ❌ Credits | ✅ Yes |
| **Open Source** | ❌ | ✅ Yes |
| **Video Recording** | ❓ | ✅ Yes |
| **Custom Images** | ❓ | ✅ Yes |

**Scrapybara Windows Notes:**
- Windows 11 desktop environment
- Interactive streaming
- Slower startup time than Linux
- **Double compute cost** (disadvantage we can exploit)

#### Mobile Testing Platforms

| Platform | Android | iOS | AI/MCP | Price |
|----------|:-------:|:---:|:------:|-------|
| **BrowserStack** | ✅ | ✅ | ❌ | $249/mo |
| **Sauce Labs** | ✅ | ✅ | ❌ | $199/mo |
| **AWS Device Farm** | ✅ | ✅ | ❌ | $0.17-0.68/min |
| **LambdaTest** | ✅ | ✅ | ❌ | Contact |
| **DeskCloud** | ✅ Planned | ❌ | ✅ | $29-99/mo |

**DeskCloud Advantage:** AI-native with BYOK = 5-10x cheaper

#### Windows RPA Platforms

| Platform | AI-Native | BYOK | Open Source | Price |
|----------|:---------:|:----:|:-----------:|-------|
| **UiPath** | Partial | ❌ | ❌ | $500+/mo |
| **Automation Anywhere** | Partial | ❌ | ❌ | $500+/mo |
| **Power Automate** | Partial | ❌ | ❌ | $15-40/user/mo |
| **Scrapybara** | ✅ | ❌ | ❌ | $29-99/mo (2x) |
| **DeskCloud** | ✅ | ✅ | ✅ | $29-99/mo |

---

## Supported Operating Systems

### Priority Matrix

```
                    HIGH VALUE
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
    │    ANDROID        │     WINDOWS       │
    │    ★★★★★          │     ★★★☆☆         │
    │    Phase 5        │     Phase 7       │
    │  (No AI+BYOK      │   (Scrapybara     │
    │   competitors)    │    already has)   │
    │                   │                   │
LOW ├───────────────────┼───────────────────┤ HIGH
EFFORT                  │                   EFFORT
    │                   │                   │
    │  RASPBERRY PI     │     macOS         │
    │    ★★★★☆          │     ★☆☆☆☆         │
    │    Phase 6        │     Not planned   │
    │  (Unique in       │                   │
    │   market!)        │                   │
    │                   │                   │
    └───────────────────┼───────────────────┘
                        │
                    LOW VALUE
```

### Strategic Rationale for Priority Order

> **Cost-Efficient Strategy:** Focus on what can run on Render.com + Vercel first. Defer dedicated server requirements (Android, Windows) to future phases when revenue supports infrastructure expansion.

| Priority | OS | Infrastructure | Rationale |
|:--------:|-----|:--------------:|-----------|
| **1st** | **Raspberry Pi** | Render.com ✅ | Runs on current infra, unique in market, low effort |
| **Future** | **Android** | Dedicated Server 💰 | Needs KVM - defer until revenue supports ~$40+/mo server |
| **Future** | **Windows** | Dedicated Server 💰 | Needs KVM, Scrapybara already has it - lowest priority |

### OS Support Summary

| OS | Version | Display Tech | Automation | Infrastructure | Status |
|----|---------|--------------|------------|:--------------:|--------|
| **Ubuntu** | 22.04, 24.04 | Xvfb + VNC | PyAutoGUI, xdotool | Render.com | ✅ Current |
| **Raspberry Pi** | Bookworm | QEMU + VNC | PyAutoGUI, GPIO | Render.com | 🔜 Phase 6 |
| **Android** | 11-14 | Scrcpy | ADB, UI Automator | Dedicated 💰 | 📋 Future |
| **Windows** | 10, 11, Server | RDP/VNC | PyAutoGUI | Dedicated 💰 | 📋 Future |
| **macOS** | - | - | - | Apple HW | ❌ Blocked |

### Infrastructure Cost Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1-6: COST-EFFICIENT                    │
│                    (Render.com + Vercel Only)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Vercel (Frontend)           Render.com (Backend)              │
│  ├── Landing Page            ├── FastAPI Backend               │
│  ├── Dashboard               ├── Ubuntu Sessions ✅            │
│  └── ~$20/mo (Pro)           ├── Raspberry Pi Sessions ✅      │
│                              └── ~$50-100/mo                   │
│                                                                 │
│  Total: ~$70-120/month                                          │
│  No dedicated servers needed!                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    FUTURE: WHEN REVENUE SUPPORTS                │
│                    (Add Dedicated Servers)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Existing Infrastructure     + Dedicated Server                │
│  (Render + Vercel)             (Hetzner/OVH ~$40-100/mo)       │
│                                ├── Android Emulators           │
│                                └── (Windows if needed)         │
│                                                                 │
│  Trigger: When MRR > $500/month OR strong customer demand      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Overview

### Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SessionManager                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  DisplayManager │  │   AgentRunner   │  │FilesystemManager│ │
│  │  (X11/VNC only) │  │                 │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Extended Architecture (Multi-OS)

```
┌─────────────────────────────────────────────────────────────────┐
│                        SessionManager                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                  DisplayBackendFactory                      ││
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ ││
│  │  │   X11      │ │  Android   │ │  Windows   │ │Raspberry │ ││
│  │  │  Backend   │ │  Backend   │ │  Backend   │ │ Backend  │ ││
│  │  │(Xvfb+VNC)  │ │(Scrcpy+ADB)│ │(RDP/VNC)   │ │(QEMU+VNC)│ ││
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   ToolAdapterFactory                        ││
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ ││
│  │  │  X11Tools  │ │  ADBTools  │ │WindowsTools│ │ GPIOTools│ ││
│  │  │(PyAutoGUI) │ │(adb, uiauto)│ │(PyAutoGUI) │ │(RPi.GPIO)│ ││
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────────────────────────────┐│
│  │   AgentRunner   │  │         FilesystemManager              ││
│  │   (unchanged)   │  │  (adapts per OS - ext4, NTFS, etc.)   ││
│  └─────────────────┘  └─────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Abstract Interfaces

```python
# app/services/backends/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class DisplayInfo:
    """Universal display info across all backends."""
    session_id: str
    os_type: str  # "linux", "android", "windows", "raspbian"
    display_url: str  # VNC/Scrcpy/RDP URL
    width: int
    height: int
    is_ready: bool = False


class DisplayBackend(ABC):
    """Abstract interface for OS-specific display backends."""
    
    @property
    @abstractmethod
    def os_type(self) -> str:
        """Return the OS type identifier."""
        pass
    
    @abstractmethod
    async def create_instance(self, session_id: str, config: dict) -> DisplayInfo:
        """Create a new OS instance for the session."""
        pass
    
    @abstractmethod
    async def destroy_instance(self, session_id: str) -> None:
        """Destroy the OS instance."""
        pass
    
    @abstractmethod
    async def get_screenshot(self, session_id: str) -> bytes:
        """Capture screenshot of the display."""
        pass
    
    @abstractmethod
    async def get_display_info(self, session_id: str) -> Optional[DisplayInfo]:
        """Get current display information."""
        pass


class ToolAdapter(ABC):
    """Abstract interface for OS-specific automation tools."""
    
    @abstractmethod
    async def click(self, x: int, y: int, button: str = "left") -> None:
        """Click at coordinates."""
        pass
    
    @abstractmethod
    async def type_text(self, text: str) -> None:
        """Type text."""
        pass
    
    @abstractmethod
    async def key_press(self, key: str) -> None:
        """Press a key."""
        pass
    
    @abstractmethod
    async def scroll(self, x: int, y: int, direction: str, amount: int) -> None:
        """Scroll at coordinates."""
        pass
    
    @abstractmethod
    async def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> None:
        """Drag from start to end coordinates."""
        pass
```

---

## Android Support

### Overview

Provide Android emulator instances for AI agents to automate mobile apps.

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Emulator** | Android Emulator (QEMU) | Run Android OS |
| **Container** | dockerify-android / Google scripts | Docker packaging |
| **Display** | Scrcpy | Screen streaming (like VNC) |
| **Automation** | ADB (Android Debug Bridge) | Input/control |
| **UI Inspection** | UI Automator / Appium | Element detection |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Android Instance                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Docker Container                          │  │
│  │  ┌──────────────────────────────────────────────────────┐│  │
│  │  │            Android Emulator (QEMU)                   ││  │
│  │  │  ┌────────────────────────────────────────────────┐  ││  │
│  │  │  │              Android 13/14                     │  ││  │
│  │  │  │  ┌─────────────────────────────────────────┐   │  ││  │
│  │  │  │  │           User Apps                     │   │  ││  │
│  │  │  │  │  (installed via ADB)                    │   │  ││  │
│  │  │  │  └─────────────────────────────────────────┘   │  ││  │
│  │  │  └────────────────────────────────────────────────┘  ││  │
│  │  └──────────────────────────────────────────────────────┘│  │
│  │                          │                                │  │
│  │              ┌───────────┴───────────┐                   │  │
│  │              ▼                       ▼                   │  │
│  │  ┌──────────────────┐    ┌──────────────────┐            │  │
│  │  │     Scrcpy       │    │       ADB        │            │  │
│  │  │  (Display Stream)│    │   (Automation)   │            │  │
│  │  │   Port: 5900+N   │    │   Port: 5555+N   │            │  │
│  │  └──────────────────┘    └──────────────────┘            │  │
│  │              │                       │                   │  │
│  └──────────────┼───────────────────────┼───────────────────┘  │
│                 │                       │                      │
│                 ▼                       ▼                      │
│           Web Viewer              MCP Tools                    │
│          (Dashboard)            (AI Agent)                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Android Backend Implementation

```python
# app/services/backends/android.py

import asyncio
import subprocess
from dataclasses import dataclass
from typing import Optional

from .base import DisplayBackend, DisplayInfo


@dataclass
class AndroidConfig:
    """Configuration for Android instance."""
    android_version: str = "13"  # Android 13
    device_profile: str = "pixel_6"  # Emulator profile
    screen_width: int = 1080
    screen_height: int = 2400
    dpi: int = 420


class AndroidDisplayBackend(DisplayBackend):
    """Android emulator backend using Scrcpy for display."""
    
    def __init__(self):
        self.instances: dict[str, AndroidInstance] = {}
    
    @property
    def os_type(self) -> str:
        return "android"
    
    async def create_instance(self, session_id: str, config: dict) -> DisplayInfo:
        android_config = AndroidConfig(**config.get("android", {}))
        
        # Start Android emulator container
        container_id = await self._start_emulator_container(
            session_id, 
            android_config
        )
        
        # Wait for emulator to boot
        await self._wait_for_boot(container_id)
        
        # Start Scrcpy for display streaming
        scrcpy_port = await self._start_scrcpy(container_id, session_id)
        
        # Store instance info
        instance = AndroidInstance(
            session_id=session_id,
            container_id=container_id,
            scrcpy_port=scrcpy_port,
            adb_port=5555 + self._get_instance_num(session_id),
            config=android_config
        )
        self.instances[session_id] = instance
        
        return DisplayInfo(
            session_id=session_id,
            os_type="android",
            display_url=f"ws://localhost:{scrcpy_port}",
            width=android_config.screen_width,
            height=android_config.screen_height,
            is_ready=True
        )
    
    async def get_screenshot(self, session_id: str) -> bytes:
        instance = self.instances.get(session_id)
        if not instance:
            raise ValueError(f"No Android instance for session {session_id}")
        
        # Use ADB to capture screenshot
        result = await asyncio.create_subprocess_exec(
            "adb", "-s", f"localhost:{instance.adb_port}",
            "exec-out", "screencap", "-p",
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await result.communicate()
        return stdout
    
    async def _start_emulator_container(
        self, 
        session_id: str, 
        config: AndroidConfig
    ) -> str:
        """Start Android emulator in Docker container."""
        cmd = [
            "docker", "run", "-d",
            "--name", f"deskcloud-android-{session_id}",
            "--device", "/dev/kvm",  # KVM acceleration
            "-p", f"{5555 + self._get_instance_num(session_id)}:5555",
            "-e", f"ANDROID_VERSION={config.android_version}",
            "-e", f"DEVICE={config.device_profile}",
            "deskcloud/android-emulator:latest"
        ]
        result = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await result.communicate()
        return stdout.decode().strip()
```

### Android Tool Adapter

```python
# app/services/tools/android.py

import asyncio
from .base import ToolAdapter


class ADBToolAdapter(ToolAdapter):
    """Tool adapter for Android using ADB commands."""
    
    def __init__(self, adb_host: str, adb_port: int):
        self.adb_target = f"{adb_host}:{adb_port}"
    
    async def _adb(self, *args) -> str:
        """Execute ADB command."""
        cmd = ["adb", "-s", self.adb_target] + list(args)
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await result.communicate()
        return stdout.decode()
    
    async def click(self, x: int, y: int, button: str = "left") -> None:
        await self._adb("shell", "input", "tap", str(x), str(y))
    
    async def type_text(self, text: str) -> None:
        # Escape special characters for ADB
        escaped = text.replace(" ", "%s").replace("'", "\\'")
        await self._adb("shell", "input", "text", escaped)
    
    async def key_press(self, key: str) -> None:
        # Map common keys to Android keycodes
        keycode_map = {
            "enter": "66",
            "back": "4",
            "home": "3",
            "menu": "82",
            "tab": "61",
            "escape": "111",
        }
        keycode = keycode_map.get(key.lower(), key)
        await self._adb("shell", "input", "keyevent", keycode)
    
    async def scroll(self, x: int, y: int, direction: str, amount: int) -> None:
        # Calculate end coordinates for swipe
        if direction == "up":
            end_y = y - amount
            end_x = x
        elif direction == "down":
            end_y = y + amount
            end_x = x
        elif direction == "left":
            end_x = x - amount
            end_y = y
        else:  # right
            end_x = x + amount
            end_y = y
        
        await self._adb(
            "shell", "input", "swipe",
            str(x), str(y), str(end_x), str(end_y), "300"
        )
    
    async def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> None:
        await self._adb(
            "shell", "input", "swipe",
            str(start_x), str(start_y), str(end_x), str(end_y), "500"
        )
    
    # Android-specific methods
    
    async def install_apk(self, apk_path: str) -> None:
        """Install an APK file."""
        await self._adb("install", "-r", apk_path)
    
    async def launch_app(self, package: str, activity: str = None) -> None:
        """Launch an Android app."""
        if activity:
            await self._adb(
                "shell", "am", "start", "-n", f"{package}/{activity}"
            )
        else:
            await self._adb(
                "shell", "monkey", "-p", package, "-c",
                "android.intent.category.LAUNCHER", "1"
            )
    
    async def get_ui_hierarchy(self) -> str:
        """Get UI hierarchy XML for element detection."""
        await self._adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
        return await self._adb("shell", "cat", "/sdcard/ui.xml")
```

### Use Cases

| Use Case | Description | Example |
|----------|-------------|---------|
| **App Testing** | Test mobile app functionality | "Test login flow in MyApp" |
| **UI Automation** | Automate repetitive tasks | "Fill out form in banking app" |
| **Scraping** | Extract data from apps | "Get all notifications" |
| **Multi-device** | Test across versions | Android 11, 12, 13, 14 |
| **CI/CD** | Automated testing pipelines | Run on every commit |

---

## Windows Support

### Overview

Provide Windows 10/11 desktop instances for automating Windows applications.

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Virtualization** | QEMU/KVM via Dockur | Run Windows |
| **Container** | Docker + Dockur | Packaging |
| **Display** | VNC or RDP | Remote access |
| **Automation** | PyAutoGUI | Input control |
| **UI Inspection** | pywinauto, LDTP | Element detection |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Windows Instance                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Docker Container                          │  │
│  │  ┌──────────────────────────────────────────────────────┐│  │
│  │  │                QEMU/KVM                              ││  │
│  │  │  ┌────────────────────────────────────────────────┐  ││  │
│  │  │  │           Windows 10/11                        │  ││  │
│  │  │  │  ┌─────────────────────────────────────────┐   │  ││  │
│  │  │  │  │   Desktop Apps (Excel, SAP, etc.)       │   │  ││  │
│  │  │  │  └─────────────────────────────────────────┘   │  ││  │
│  │  │  └────────────────────────────────────────────────┘  ││  │
│  │  └──────────────────────────────────────────────────────┘│  │
│  │                          │                                │  │
│  │              ┌───────────┴───────────┐                   │  │
│  │              ▼                       ▼                   │  │
│  │  ┌──────────────────┐    ┌──────────────────┐            │  │
│  │  │   VNC Server     │    │  RDP (optional)  │            │  │
│  │  │   Port: 5900+N   │    │   Port: 3389     │            │  │
│  │  └──────────────────┘    └──────────────────┘            │  │
│  │              │                                            │  │
│  └──────────────┼────────────────────────────────────────────┘  │
│                 │                                               │
│                 ▼                                               │
│           noVNC Viewer                                          │
│           (Dashboard)                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Windows Backend Implementation

```python
# app/services/backends/windows.py

import asyncio
from dataclasses import dataclass
from typing import Optional

from .base import DisplayBackend, DisplayInfo


@dataclass  
class WindowsConfig:
    """Configuration for Windows instance."""
    version: str = "win11"  # win10, win11, win2022 (server)
    ram_gb: int = 4
    cpu_cores: int = 2
    disk_gb: int = 64
    screen_width: int = 1920
    screen_height: int = 1080


class WindowsDisplayBackend(DisplayBackend):
    """Windows VM backend using Dockur."""
    
    def __init__(self):
        self.instances: dict[str, WindowsInstance] = {}
    
    @property
    def os_type(self) -> str:
        return "windows"
    
    async def create_instance(self, session_id: str, config: dict) -> DisplayInfo:
        windows_config = WindowsConfig(**config.get("windows", {}))
        
        # Calculate ports
        instance_num = self._get_instance_num(session_id)
        vnc_port = 8006 + instance_num
        rdp_port = 3389 + instance_num
        
        # Start Windows container (Dockur)
        container_id = await self._start_windows_container(
            session_id,
            windows_config,
            vnc_port,
            rdp_port
        )
        
        # Wait for Windows to boot (this takes longer than Linux!)
        await self._wait_for_boot(container_id, timeout=300)  # 5 min timeout
        
        instance = WindowsInstance(
            session_id=session_id,
            container_id=container_id,
            vnc_port=vnc_port,
            rdp_port=rdp_port,
            config=windows_config
        )
        self.instances[session_id] = instance
        
        return DisplayInfo(
            session_id=session_id,
            os_type="windows",
            display_url=f"http://localhost:{vnc_port}",
            width=windows_config.screen_width,
            height=windows_config.screen_height,
            is_ready=True
        )
    
    async def _start_windows_container(
        self,
        session_id: str,
        config: WindowsConfig,
        vnc_port: int,
        rdp_port: int
    ) -> str:
        """Start Windows VM in Docker using Dockur."""
        cmd = [
            "docker", "run", "-d",
            "--name", f"deskcloud-windows-{session_id}",
            "--device", "/dev/kvm",
            "--cap-add", "NET_ADMIN",
            "-p", f"{vnc_port}:8006",  # Dockur VNC web port
            "-p", f"{rdp_port}:3389",  # RDP port
            "-e", f"VERSION={config.version}",
            "-e", f"RAM_SIZE={config.ram_gb}G",
            "-e", f"CPU_CORES={config.cpu_cores}",
            "-e", f"DISK_SIZE={config.disk_gb}G",
            "-v", f"deskcloud-win-{session_id}:/storage",  # Persistent storage
            "dockurr/windows:latest"
        ]
        result = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await result.communicate()
        return stdout.decode().strip()
    
    async def get_screenshot(self, session_id: str) -> bytes:
        """Capture screenshot from Windows VM."""
        instance = self.instances.get(session_id)
        if not instance:
            raise ValueError(f"No Windows instance for session {session_id}")
        
        # Use VNC to capture screenshot
        # Or use PowerShell remoting if available
        return await self._capture_vnc_screenshot(instance.vnc_port)
```

### Windows Tool Adapter

```python
# app/services/tools/windows.py

import asyncio
from .base import ToolAdapter


class WindowsToolAdapter(ToolAdapter):
    """Tool adapter for Windows using PyAutoGUI (over VNC) or PowerShell."""
    
    def __init__(self, vnc_connection):
        self.vnc = vnc_connection
    
    async def click(self, x: int, y: int, button: str = "left") -> None:
        # Send mouse click via VNC protocol
        await self.vnc.send_mouse_click(x, y, button)
    
    async def type_text(self, text: str) -> None:
        # Send keystrokes via VNC
        for char in text:
            await self.vnc.send_key(char)
    
    async def key_press(self, key: str) -> None:
        # Map to Windows virtual key codes
        await self.vnc.send_special_key(key)
    
    async def scroll(self, x: int, y: int, direction: str, amount: int) -> None:
        delta = -amount if direction in ["up", "left"] else amount
        await self.vnc.send_scroll(x, y, delta)
    
    async def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> None:
        await self.vnc.send_mouse_drag(start_x, start_y, end_x, end_y)
    
    # Windows-specific methods
    
    async def run_powershell(self, script: str) -> str:
        """Execute PowerShell script."""
        # Via WinRM or VNC keyboard input
        pass
    
    async def install_software(self, installer_path: str) -> None:
        """Install software (silent install)."""
        pass
    
    async def open_application(self, app_name: str) -> None:
        """Open Windows application."""
        # Win+R, type app name, Enter
        await self.key_press("win+r")
        await asyncio.sleep(0.5)
        await self.type_text(app_name)
        await self.key_press("enter")
```

### Use Cases

| Use Case | Description | Example |
|----------|-------------|---------|
| **SAP Automation** | Automate SAP GUI | "Create purchase order" |
| **Excel Automation** | Complex spreadsheet tasks | "Generate monthly report" |
| **Legacy Apps** | Windows-only business software | "Process insurance claim" |
| **Desktop Testing** | Test Windows applications | "Test installer workflow" |
| **Admin Tasks** | System administration | "Configure Active Directory" |

### Licensing Considerations

> ⚠️ **Important:** Running Windows requires valid licensing.

| Scenario | License Requirement |
|----------|---------------------|
| Development/Testing | Windows 10/11 Pro license |
| Production | Windows Server or VDA license |
| Enterprise | Volume licensing |

**Recommendation:** Users must provide their own Windows license, or we offer Windows Server instances with licensing included (at higher cost).

---

## Raspberry Pi Support

### Overview

Provide Raspberry Pi OS (Raspbian) emulation for IoT and embedded development.

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Emulation** | QEMU ARM | ARM emulation |
| **Container** | Docker + qemu-arm | Packaging |
| **Display** | VNC | Remote access |
| **Automation** | PyAutoGUI | Input control |
| **Hardware** | GPIO simulation | Virtual GPIO pins |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Raspberry Pi Instance                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Docker Container                          │  │
│  │  ┌──────────────────────────────────────────────────────┐│  │
│  │  │                QEMU ARM                              ││  │
│  │  │  ┌────────────────────────────────────────────────┐  ││  │
│  │  │  │         Raspberry Pi OS (Bookworm)             │  ││  │
│  │  │  │  ┌─────────────────────────────────────────┐   │  ││  │
│  │  │  │  │   Desktop + GPIO Simulation             │   │  ││  │
│  │  │  │  └─────────────────────────────────────────┘   │  ││  │
│  │  │  └────────────────────────────────────────────────┘  ││  │
│  │  └──────────────────────────────────────────────────────┘│  │
│  │                          │                                │  │
│  │              ┌───────────┴───────────┐                   │  │
│  │              ▼                       ▼                   │  │
│  │  ┌──────────────────┐    ┌──────────────────┐            │  │
│  │  │   VNC Server     │    │  GPIO Simulator  │            │  │
│  │  │   Port: 5900+N   │    │  (Virtual Pins)  │            │  │
│  │  └──────────────────┘    └──────────────────┘            │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Use Cases

| Use Case | Description | Example |
|----------|-------------|---------|
| **IoT Development** | Develop Pi applications | Home automation scripts |
| **GPIO Testing** | Test hardware interfaces | LED, sensor logic |
| **CI/CD for Pi** | Automated testing | Test before deploy |
| **Education** | Learn Pi development | No hardware needed |

---

## macOS Considerations

### Why macOS is Difficult

| Issue | Details |
|-------|---------|
| **Apple Licensing** | macOS may only run on Apple hardware |
| **No official Docker** | No legal way to run macOS in Docker |
| **Hardware requirement** | Need Mac hosts |
| **Cost** | Mac cloud providers expensive ($50+/mo) |

### Possible Approaches

1. **Mac Cloud Providers**
   - MacStadium, AWS EC2 Mac, MacinCloud
   - Very expensive ($1-2/hour)
   - We'd be reselling at loss

2. **Hackintosh (NOT recommended)**
   - Violates Apple EULA
   - Legal risk
   - Unstable

3. **Skip macOS**
   - Focus on Linux, Android, Windows
   - Address 95%+ of use cases
   - Revisit if Apple changes licensing

**Recommendation:** Do not support macOS initially. Revisit if:
- Apple changes licensing terms
- Mac cloud prices drop significantly
- Customer demand justifies cost

---

## API & Protocol Design

### Session Creation with OS Selection

```yaml
# POST /api/v1/sessions
Request:
  title: "Windows Automation Task"
  os_type: "windows"  # NEW FIELD
  os_config:          # NEW FIELD
    version: "win11"
    ram_gb: 4
    cpu_cores: 2

Response:
  id: "sess_abc123"
  os_type: "windows"
  status: "creating"
  display_url: null  # Set when ready
  estimated_boot_time: 120  # seconds

---

# GET /api/v1/sessions/{id}
Response:
  id: "sess_abc123"
  os_type: "windows"
  status: "active"
  display_url: "http://localhost:8006/vnc.html"
  os_info:
    version: "Windows 11 Pro"
    architecture: "x86_64"
    ram_mb: 4096
```

### OS-Specific Tools

```yaml
# MCP Tool Definitions (extend existing)

# Android-specific
- name: adb_install_apk
  description: Install APK on Android
  parameters:
    apk_url: string

- name: adb_launch_app
  description: Launch Android app
  parameters:
    package: string
    activity: string (optional)

- name: adb_get_ui_hierarchy
  description: Get UI element tree
  
# Windows-specific
- name: powershell
  description: Run PowerShell command
  parameters:
    script: string

- name: windows_open_app
  description: Open Windows application
  parameters:
    app_name: string

# Raspberry Pi-specific
- name: gpio_set_pin
  description: Set GPIO pin state
  parameters:
    pin: integer
    state: boolean

- name: gpio_read_pin
  description: Read GPIO pin state
  parameters:
    pin: integer
```

---

## Pricing Strategy

### Compute Cost Multipliers

| OS | Compute Multiplier | Rationale |
|----|-------------------|-----------|
| **Ubuntu/Linux** | 1.0x (baseline) | Lightweight |
| **Android** | 1.5x | Emulator overhead |
| **Windows** | 2.0x | Heavy, licensing concerns |
| **Raspberry Pi** | 1.2x | ARM emulation |

### Tier Pricing with Multi-OS

| Feature | Free | Pro $29 | Team $99 | Enterprise |
|---------|:----:|:-------:|:--------:|:----------:|
| **Ubuntu** | ✅ 1 session | ✅ 5 | ✅ 20 | Unlimited |
| **Android** | ❌ | ✅ 2 | ✅ 10 | Unlimited |
| **Windows** | ❌ | ✅ 1 | ✅ 5 | Unlimited |
| **Raspberry Pi** | ❌ | ✅ 2 | ✅ 10 | Unlimited |

### Compute Hour Calculation

```
Effective Hours = Raw Hours × OS Multiplier

Example (Pro tier, 100 compute hours):
- 100 hours of Ubuntu, OR
- 66 hours of Android, OR
- 50 hours of Windows, OR
- 83 hours of Raspberry Pi
```

### Comparison with Competitors

| OS | Scrapybara | BrowserStack | DeskCloud |
|----|------------|--------------|-----------|
| **Linux** | $29/100hr | N/A | $29/100hr |
| **Windows** | $29/50hr (2x) | N/A | $29/50hr |
| **Android** | ❓ | $249/mo | $29/66hr |
| **BYOK** | ❌ | ❌ | ✅ |

**DeskCloud advantage:** Same or better pricing PLUS BYOK model.

---

## Implementation Roadmap

> **Cost-Efficient Approach:** Focus on Render.com-compatible OS first. Defer Android/Windows until revenue supports dedicated server costs (~$40-100/mo).

### Phase 6: Raspberry Pi Support (2-3 weeks) ⭐ CURRENT PRIORITY

**Why Now:** 
- ✅ Runs on Render.com (no extra infrastructure cost)
- ✅ Completely UNIQUE in market - NO competitor offers this
- ✅ Low effort, high differentiation
- ✅ Appeals to IoT developers, makers, educators

```
Week 1:
├── [ ] Abstract DisplayBackend interface (shared with future OS)
├── [ ] QEMU ARM backend implementation
├── [ ] Raspberry Pi OS prebuilt images
├── [ ] VNC integration
└── [ ] Basic automation (PyAutoGUI)

Week 2:
├── [ ] GPIO simulation library
├── [ ] Raspberry Pi tool adapter
├── [ ] Dashboard integration (OS selector)
├── [ ] Prebuilt image templates:
│       ├── raspbian-base (minimal)
│       ├── raspbian-desktop (LXDE)
│       ├── raspbian-dev (Python, Node)
│       └── raspbian-iot (MQTT, sensors)
└── [ ] Documentation

Week 3:
├── [ ] Testing across Pi versions (3, 4, 5 emulation)
├── [ ] Performance optimization
├── [ ] Beta launch with "Raspberry Pi" badge
└── [ ] Production deployment
```

---

### 📋 FUTURE: Android Support (4-6 weeks)

> **⚠️ DEFERRED:** Requires dedicated server with KVM (~$40-100/month). Implement when MRR > $500/month OR strong customer demand.

**Trigger Conditions:**
- [ ] Monthly recurring revenue exceeds $500
- [ ] 10+ customer requests for Android support
- [ ] Strategic partnership opportunity

**When Ready:**
```
Week 1:
├── [ ] Provision dedicated server (Hetzner/OVH)
├── [ ] Android backend skeleton
├── [ ] Docker image with Android emulator
└── [ ] Basic ADB integration

Week 2:
├── [ ] Scrcpy integration for display
├── [ ] ADB tool adapter
├── [ ] Screenshot capture
└── [ ] Basic input (click, type)

Week 3:
├── [ ] UI hierarchy inspection
├── [ ] App installation via ADB
├── [ ] App launch functionality
└── [ ] Dashboard integration

Week 4:
├── [ ] Multiple Android versions
├── [ ] Device profiles
├── [ ] Performance optimization
└── [ ] Testing & bug fixes

Week 5-6:
├── [ ] Documentation
├── [ ] Customer beta testing
├── [ ] Pricing integration (compute multiplier)
└── [ ] Production deployment
```

---

### 📋 FUTURE: Windows Support (6-8 weeks)

> **⚠️ DEFERRED:** Requires dedicated server with KVM. Lower priority since Scrapybara already offers Windows. Implement only if clear market demand.

**Trigger Conditions:**
- [ ] Android support stable and generating revenue
- [ ] Enterprise customer requests Windows specifically
- [ ] Competitive pressure requires feature parity

**When Ready:**
```
Week 1-2:
├── [ ] Windows backend skeleton
├── [ ] Dockur/QEMU integration
├── [ ] VNC/RDP setup
└── [ ] Basic boot process

Week 3-4:
├── [ ] Windows tool adapter
├── [ ] Screenshot capture
├── [ ] Input handling
└── [ ] Application launching

Week 5-6:
├── [ ] PowerShell integration
├── [ ] Software installation
├── [ ] Dashboard integration
└── [ ] Windows versions (10, 11, Server)

Week 7-8:
├── [ ] Performance optimization
├── [ ] Licensing documentation
├── [ ] Testing & bug fixes
└── [ ] Production deployment
```

---

## Infrastructure Requirements

### Multi-Session Resource Requirements

| OS | RAM per Session | Sessions per 8GB Host | Sessions per 64GB Host |
|----|-----------------|:---------------------:|:----------------------:|
| **Ubuntu** | 50-100MB | 20-40 | 200+ |
| **Raspberry Pi** | 512MB-1GB | 4-8 | 32-64 |
| **Android** | 2-4GB | ❌ (needs KVM) | 8-16 |
| **Windows** | 4-8GB | ❌ (needs KVM) | 4-8 |

### Multi-Session Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SESSION ORCHESTRATOR                       │
│                    (Render.com Backend)                         │
│                                                                 │
│  Create Session Request:                                        │
│  { os_type: "android", user_id: "user123" }                    │
│                              │                                  │
│              ┌───────────────┼───────────────┐                  │
│              ▼               ▼               ▼                  │
│       ┌───────────┐   ┌───────────┐   ┌───────────┐            │
│       │  Ubuntu   │   │Raspberry  │   │  Android  │            │
│       │   Pool    │   │  Pi Pool  │   │   Pool    │            │
│       │ (Render)  │   │ (Render)  │   │(Dedicated)│            │
│       │  20-40    │   │   4-8     │   │   8-16    │            │
│       │ sessions  │   │ sessions  │   │ sessions  │            │
│       └───────────┘   └───────────┘   └───────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Host Requirements by OS

| OS | vCPU | RAM | Storage | KVM Required | Runs on Render? |
|----|------|-----|---------|:------------:|:---------------:|
| **Ubuntu** | 2 | 2GB | 10GB | No | ✅ Yes |
| **Raspberry Pi** | 1-2 | 512MB-1GB | 8GB | No | ✅ Yes (slower) |
| **Android** | 2-4 | 2-4GB | 20GB | **Yes** | ❌ No |
| **Windows** | 2-4 | 4-8GB | 64GB | **Yes** | ❌ No |

### Infrastructure Strategy: Hybrid Approach

```
┌─────────────────────────────────────────────────────────────────┐
│                      RENDER.COM                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  FastAPI Backend + Dashboard                               │ │
│  │  ├── Auth, API Keys, Billing                              │ │
│  │  ├── Session Orchestration                                │ │
│  │  └── Database (Vercel Postgres)                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│              ┌───────────────┴───────────────┐                 │
│              ▼                               ▼                 │
│  ┌──────────────────────┐    ┌──────────────────────┐         │
│  │   Ubuntu Workers     │    │  Raspberry Pi        │         │
│  │   (Native Docker)    │    │  (QEMU ARM)          │         │
│  │   ✅ 20-40 sessions  │    │  ⚠️ 4-8 sessions     │         │
│  └──────────────────────┘    └──────────────────────┘         │
│                                                                 │
│  Monthly Cost: ~$50-100                                         │
│  KVM: Not required                                              │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
        ┌──────────────────────┐  ┌──────────────────────┐
        │  DEDICATED SERVER    │  │   (Scale as needed)  │
        │  (with KVM support)  │  │   More servers       │
        │                      │  │                      │
        │  Android Emulators   │  │  Android/Windows     │
        │  8-16 sessions       │  │  additional capacity │
        │                      │  │                      │
        │  Monthly: ~$40-100   │  │                      │
        └──────────────────────┘  └──────────────────────┘
```

### Dedicated Server Providers Comparison

For Android support (requires KVM), these providers offer affordable dedicated servers:

#### Budget Options (Recommended for Starting)

| Provider | Server | RAM | Monthly Cost | Location | KVM |
|----------|--------|-----|--------------|----------|:---:|
| **Hetzner** | AX41 (Ryzen 5 3600) | 64GB | ~$40 | EU, USA | ✅ |
| **Hetzner** | AX52 (Ryzen 7 5700X) | 64GB | ~$55 | EU, USA | ✅ |
| **OVH** | Rise-1 (Intel i5) | 32GB | ~$60 | EU, USA, CA | ✅ |
| **OVH** | Advance-1 (Intel i7) | 64GB | ~$100 | EU, USA, CA | ✅ |
| **Contabo** | Dedicated (AMD Ryzen) | 64GB | ~$50 | EU, USA | ✅ |
| **HOSTKEY** | Entry Dedicated | 32GB | ~$25 | EU, USA | ✅ |

#### Premium Options (More Support/Locations)

| Provider | Server | RAM | Monthly Cost | Location | KVM |
|----------|--------|-----|--------------|----------|:---:|
| **Vultr Bare Metal** | E-2286G | 64GB | ~$185 | Global | ✅ |
| **AWS EC2** | c5.metal | 192GB | ~$300+ | Global | ✅ |
| **GCP** | n2-standard-32 | 128GB | ~$400+ | Global | ✅ |

#### Why These Providers?

| Provider | Pros | Cons |
|----------|------|------|
| **Hetzner** | Cheapest, great specs, reliable | EU-focused (USA available) |
| **OVH** | Good value, global presence | Slower support |
| **Vultr** | Easy to use, global | More expensive |
| **AWS/GCP** | Enterprise, global, managed | 5-10x more expensive |

> **Recommendation:** Start with Hetzner or OVH for best price-to-performance. Scale to Vultr/AWS if you need more regions or enterprise features.

### Provider Compatibility Matrix

| Provider | Ubuntu | Raspberry Pi | Android | Windows |
|----------|:------:|:------------:|:-------:|:-------:|
| **Render.com** | ✅ | ✅ (slower) | ❌ | ❌ |
| **Hetzner Dedicated** | ✅ | ✅ | ✅ | ✅ |
| **OVH Dedicated** | ✅ | ✅ | ✅ | ✅ |
| **Vultr Bare Metal** | ✅ | ✅ | ✅ | ✅ |
| **AWS EC2 Metal** | ✅ | ✅ | ✅ | ✅ |
| **DigitalOcean** | ✅ | ⚠️ | ❌ | ❌ |

### Capacity Planning Examples

#### Starter Setup (~$90/month)

| Component | Provider | Sessions | Cost |
|-----------|----------|:--------:|------|
| API + Dashboard | Render.com | N/A | ~$50 |
| Ubuntu | Render.com | 20-40 | (included) |
| Raspberry Pi | Render.com | 4-8 | (included) |
| Android | Hetzner AX41 | 8-16 | ~$40 |
| **Total** | | **32-64** | **~$90/mo** |

#### Growth Setup (~$180/month)

| Component | Provider | Sessions | Cost |
|-----------|----------|:--------:|------|
| API + Dashboard | Render.com | N/A | ~$50 |
| Ubuntu | Render.com (larger) | 40-80 | ~$30 |
| Raspberry Pi | Render.com | 8-16 | (included) |
| Android | 2x Hetzner AX41 | 16-32 | ~$80 |
| **Total** | | **64-128** | **~$160/mo** |

#### Scale Setup (~$400/month)

| Component | Provider | Sessions | Cost |
|-----------|----------|:--------:|------|
| API + Dashboard | Render.com | N/A | ~$50 |
| Ubuntu | Render.com | 80+ | ~$50 |
| Raspberry Pi | Render.com | 16+ | ~$30 |
| Android (USA) | Hetzner USA | 16-32 | ~$80 |
| Android (EU) | Hetzner EU | 16-32 | ~$80 |
| **Total** | | **128-196** | **~$290/mo** |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Android emulator slow** | Medium | Medium | Optimize, offer device profiles |
| **Windows boot time long** | High | Medium | Pre-boot pools, communicate expectations |
| **Windows licensing issues** | Medium | High | Clear BYOL policy, documentation |
| **KVM not available on host** | Medium | High | Document requirements, fallback modes |
| **Scrapybara already has Windows** | High | Medium | Differentiate on BYOK, pricing |
| **Complexity overwhelms team** | Medium | Medium | Phased rollout, focus on one OS at a time |

---

## Success Metrics

### Phase 6: Raspberry Pi (Current Focus)

| Metric | Target | Notes |
|--------|--------|-------|
| **Pi sessions** | 15% of total sessions | Within 3 months of launch |
| **Pi user retention** | 40% monthly active | Sticky use case |
| **IoT community buzz** | 200+ GitHub stars | From Pi feature |
| **Boot time** | < 90 seconds | With prebuilt images |
| **Multi-session capacity** | 4-8 per Render host | Cost-efficient |

### Future: Android (When Revenue Supports)

| Metric | Target | Trigger |
|--------|--------|---------|
| Customer requests | 10+ requests | Before implementing |
| MRR threshold | > $500/month | Before adding server costs |
| Android sessions | 25% of sessions | Post-launch target |
| BrowserStack converts | 15% of mobile users | From $249 → $29 |

### Infrastructure Cost Targets

| Phase | Monthly Infra Cost | Revenue Target |
|-------|-------------------|----------------|
| **Now (Ubuntu only)** | ~$50-70 | $0+ (building) |
| **Phase 6 (+ Pi)** | ~$70-100 | $200+ |
| **Future (+ Android)** | ~$120-150 | $500+ |
| **Future (+ Windows)** | ~$160-200 | $1000+ |

> **Rule:** Don't add infrastructure until revenue covers 3x the cost.

---

## Related Plans

- [Next.js Landing & Dashboard](./nextjs_landing_dashboard.md) - Frontend for OS selection
- [Session Video Recording](./session_video_recording.md) - Works across all OS
- [Custom Image Builder](./custom_image_builder.md) - Extended for multi-OS
- [Remote Agent Client](./remote_agent_client.md) - Control user's own computers (zero compute cost)

---

## Appendix A: Docker Images

### DeskCloud Android Image

```dockerfile
# Dockerfile.android
FROM budtmo/docker-android:latest

# DeskCloud integration layer
COPY scripts/deskcloud-entrypoint.sh /opt/deskcloud/
COPY scripts/scrcpy-setup.sh /opt/deskcloud/

# Pre-configure for AI automation
ENV EMULATOR_DEVICE="pixel_6"
ENV ANDROID_VERSION="13"

ENTRYPOINT ["/opt/deskcloud/deskcloud-entrypoint.sh"]
```

### DeskCloud Windows Image

```yaml
# docker-compose.windows.yml
version: "3.8"
services:
  windows:
    image: dockurr/windows:latest
    container_name: deskcloud-windows
    devices:
      - /dev/kvm
    cap_add:
      - NET_ADMIN
    ports:
      - "8006:8006"  # VNC web
      - "3389:3389"  # RDP
    environment:
      VERSION: "win11"
      RAM_SIZE: "4G"
      CPU_CORES: "2"
    volumes:
      - windows-storage:/storage
```

---

## Appendix B: Scrapybara Windows Comparison

Based on research, Scrapybara's Windows support:

| Aspect | Scrapybara | DeskCloud (Planned) |
|--------|------------|---------------------|
| **Windows Version** | Windows 11 | Windows 10, 11, Server |
| **Boot Time** | Slower | Similar (2-3 min) |
| **Compute Cost** | 2x Linux | 2x Linux |
| **BYOK** | ❌ Credits | ✅ Yes |
| **Open Source** | ❌ | ✅ Core is open |
| **Video Recording** | ❓ | ✅ Yes |
| **Custom Images** | ❓ | ✅ Yes |

**DeskCloud differentiators for Windows:**
1. BYOK pricing model
2. Open source core
3. Video recording
4. More Windows versions (including Server)

---

*Document Version: 1.0*  
*Last Updated: December 2025*

