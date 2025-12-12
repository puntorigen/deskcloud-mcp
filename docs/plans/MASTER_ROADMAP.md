# DeskCloud Master Roadmap & Project Context

> **Purpose**: This document serves as the primary onboarding guide for AI assistants and developers. It captures all strategic decisions, technical architecture, and the complete roadmap for the DeskCloud project.
>
> **Last Updated**: December 2025  
> **Status**: Planning Phase (Pre-Implementation)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Vision](#project-vision)
3. [Business Model](#business-model)
4. [Repository Architecture](#repository-architecture)
5. [Technical Stack](#technical-stack)
6. [Feature Overview](#feature-overview)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Key Decisions Made](#key-decisions-made)
9. [Plan Documents Reference](#plan-documents-reference)
10. [Infrastructure Strategy](#infrastructure-strategy)
11. [Branding & Design](#branding--design)
12. [Getting Started (For New AI Assistants)](#getting-started-for-new-ai-assistants)

---

## Executive Summary

### What is DeskCloud?

**DeskCloud** is an MCP (Model Context Protocol) server that enables AI agents like Claude to control virtual desktops. It provides two primary modes of operation:

1. **Cloud VMs**: Isolated Ubuntu/Raspberry Pi virtual machines hosted by DeskCloud
2. **Connect Agent**: A lightweight client that lets AI control users' own Windows/macOS/Linux computers

### Core Value Proposition

| For Developers | For Enterprises |
|----------------|-----------------|
| Let Claude automate desktop tasks | RPA for legacy Windows apps |
| Test across real OS environments | Automate SAP, Salesforce, Outlook |
| IoT development with Raspberry Pi | 24/7 server automation |
| Browser + desktop app automation | Compliance with video recording |

### Business Positioning

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DeskCloud Market Position                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Browser-Only                        Full OS Control                        │
│  ◄──────────────────────────────────────────────────────────────────────►  │
│                                                                             │
│  Playwright    Browserbase    │  DeskCloud  │    Scrapybara    Windows VMs │
│  Puppeteer     Steel          │             │    E2B                        │
│                               │             │                               │
│                               │  ✓ Cloud VMs                               │
│                               │  ✓ Connect Agent (YOUR computers)          │
│                               │  ✓ Raspberry Pi (unique!)                  │
│                               │  ✓ MCP-native                              │
│                               │  ✓ Open source core                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Unique Differentiators

1. **Connect Agent**: Only solution that lets AI control YOUR computers (not just cloud VMs)
2. **Raspberry Pi**: Unique IoT/embedded development support
3. **Open Source Core**: MIT-licensed, self-hostable
4. **BYOK**: Users bring their own Anthropic API key
5. **MCP-Native**: First-class Cursor IDE and Claude Desktop support

---

## Project Vision

### The Problem

AI agents like Claude can analyze code and generate text, but they can't:
- Browse the web and interact with sites
- Use desktop applications (Outlook, SAP, Excel)
- Automate GUI-based workflows
- Control IoT devices or embedded systems

### The Solution

DeskCloud bridges this gap by providing:

1. **Isolated Environments**: Safe sandboxes for AI to operate
2. **Visual Control**: Screenshot → AI decides → execute action
3. **MCP Protocol**: Native integration with Claude/Cursor
4. **Flexibility**: Cloud VMs for isolation, Connect Agent for real apps

### Long-Term Vision

```
Phase 1 (Now):     Ubuntu cloud VMs + MCP server
Phase 2 (Q1 2026): Dashboard + Connect Agent
Phase 3 (Q2 2026): Raspberry Pi + Video Recording
Phase 4 (Q3 2026): Android + Custom Images
Phase 5 (Future):  Windows VMs + Enterprise features
```

---

## Business Model

### Open Core Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Open Core Architecture                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                     OPEN SOURCE (MIT License)                          │ │
│  │                     github.com/[org]/mcp-computer-use                  │ │
│  │                                                                        │ │
│  │  • MCP server implementation                                           │ │
│  │  • Ubuntu/Linux session management                                     │ │
│  │  • Display manager (X11/VNC)                                          │ │
│  │  • Computer use tools (screenshot, click, type)                       │ │
│  │  • Basic session API                                                   │ │
│  │  • Self-hosting instructions                                           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    │ git subtree                            │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                     PREMIUM (Hosted + Features)                        │ │
│  │                     deskcloud.app                                      │ │
│  │                                                                        │ │
│  │  • Next.js landing page & dashboard                                   │ │
│  │  • User authentication & API keys                                     │ │
│  │  • Connect Agent (control your own computers)                         │ │
│  │  • Session video recording                                            │ │
│  │  • Raspberry Pi support                                               │ │
│  │  • Custom image builder                                               │ │
│  │  • Team management                                                    │ │
│  │  • Priority support                                                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Pricing Tiers

| Tier | Price | Cloud VMs | Connect Devices | Key Features |
|------|-------|-----------|-----------------|--------------|
| **Free** | $0 | 1 concurrent | ❌ | Ubuntu only, 24h history |
| **Pro** | $29/mo | 5 concurrent | 3 devices | + Pi, Video, Unlimited remote |
| **Team** | $99/mo | 20 concurrent | 10 devices | + Custom images, Team mgmt |
| **Enterprise** | Custom | Unlimited | Unlimited | + Android, SSO, SLA |

### Revenue Streams

1. **Subscription fees** (primary)
2. **Compute usage** for cloud VMs
3. **Enterprise contracts** with SLA
4. **On-premise licenses** (future)

---

## Repository Architecture

### Two-Repository Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Repository Structure                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PUBLIC REPO: mcp-computer-use (Open Source)                               │
│  ══════════════════════════════════════════                                │
│  ├── app/                    # FastAPI backend                             │
│  │   ├── api/                # REST + MCP endpoints                        │
│  │   ├── services/           # Session, display, tools                     │
│  │   └── db/                 # SQLModel models                             │
│  ├── docs/                   # Documentation                               │
│  │   ├── plans/              # Planning documents (this folder)            │
│  │   └── api/                # API documentation                           │
│  ├── scripts/                # Setup scripts                               │
│  ├── tests/                  # Test suite                                  │
│  └── README.md               # Public documentation                        │
│                                                                             │
│                    │                                                        │
│                    │ git subtree (sync core)                               │
│                    ▼                                                        │
│                                                                             │
│  PRIVATE REPO: deskcloud-platform (Premium)                                │
│  ═══════════════════════════════════════════                               │
│  ├── core/                   # Subtree from mcp-computer-use               │
│  │   └── (synced from public repo)                                        │
│  ├── frontend/               # Next.js app                                 │
│  │   ├── app/                # Pages (landing, dashboard)                  │
│  │   ├── components/         # React components                            │
│  │   └── lib/                # Utilities                                   │
│  ├── backend-premium/        # Premium API extensions                      │
│  │   ├── auth/               # Authentication                              │
│  │   ├── devices/            # Connect Agent API                           │
│  │   ├── recording/          # Video recording                             │
│  │   └── images/             # Custom image builder                        │
│  ├── connect-agent/          # Desktop client app                          │
│  │   ├── src/                # Python agent code                           │
│  │   └── installer/          # OS-specific installers                      │
│  ├── infrastructure/         # Terraform/Docker configs                    │
│  └── README.md               # Private documentation                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Sync Strategy

```bash
# In private repo, sync changes from public open source repo
git subtree pull --prefix=core git@github.com:org/mcp-computer-use.git main --squash

# If we fix a bug in core that should go back to open source
git subtree push --prefix=core git@github.com:org/mcp-computer-use.git main
```

---

## Technical Stack

### Backend (Python/FastAPI)

| Component | Technology | Notes |
|-----------|------------|-------|
| **Framework** | FastAPI | Async, OpenAPI docs |
| **ORM** | SQLModel | SQLAlchemy + Pydantic |
| **Database** | PostgreSQL | Vercel Postgres (hosted) |
| **Auth** | JWT + HttpOnly Cookies | python-jose, passlib |
| **Hosting** | Render.com | Existing infrastructure |

### Frontend (Next.js)

| Component | Technology | Notes |
|-----------|------------|-------|
| **Framework** | Next.js 15 | App Router |
| **Styling** | Tailwind CSS | Dark mode first |
| **Components** | shadcn/ui | Consistent UI |
| **State** | TanStack Query | Server state management |
| **Forms** | React Hook Form + Zod | Validation |
| **Hosting** | Vercel Pro | Edge functions |

### Connect Agent (Python)

| Component | Technology | Notes |
|-----------|------------|-------|
| **Language** | Python 3.11+ | Cross-platform |
| **Screen Capture** | mss | Fast screenshots |
| **Input Control** | PyAutoGUI | Mouse/keyboard |
| **Networking** | websockets | Async WebSocket |
| **Encryption** | PyNaCl | E2E encryption |
| **Packaging** | PyInstaller | Single executable |
| **UI** | pystray + tkinter | System tray |

### Infrastructure

| Component | Provider | Notes |
|-----------|----------|-------|
| **Backend** | Render.com | Python/FastAPI |
| **Frontend** | Vercel Pro | Next.js |
| **Database** | Vercel Postgres | Managed PostgreSQL |
| **Video Storage** | Cloudflare R2 | S3-compatible, cheap |
| **Future: KVM** | Hetzner/OVH | For Android/Windows |

---

## Feature Overview

### Current Features (Open Source)

- ✅ MCP server with Claude computer use
- ✅ Ubuntu Linux virtual desktops
- ✅ Session management API
- ✅ X11/VNC display server
- ✅ Multi-session concurrency
- ✅ OverlayFS filesystem isolation
- ✅ BYOK (Bring Your Own Key)

### Planned Features (Premium)

| Feature | Tier | Plan Document |
|---------|------|---------------|
| User Authentication | All | `nextjs_landing_dashboard.md` |
| API Key Management | All | `nextjs_landing_dashboard.md` |
| Dashboard UI | All | `nextjs_landing_dashboard.md` |
| Connect Agent (Remote) | Pro+ | `remote_agent_client.md` |
| Server Mode (Always-On) | Pro+ | `remote_agent_client.md` |
| Raspberry Pi Support | Pro+ | `multi_os_support.md` |
| Video Recording | Pro+ | `session_video_recording.md` |
| Custom Image Builder | Team+ | `custom_image_builder.md` |
| Android Emulation | Enterprise | `multi_os_support.md` |
| Windows VMs | Enterprise | `multi_os_support.md` |

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Backend auth + database setup

- [ ] Set up Vercel Postgres database
- [ ] Implement SQLModel models (User, APIKey, RefreshToken, RemoteDevice)
- [ ] Create auth endpoints (register, login, refresh, logout)
- [ ] Add JWT middleware to existing session endpoints
- [ ] Set up CORS for frontend

**Dependencies**: None  
**Plan**: `nextjs_landing_dashboard.md` Phase 1

### Phase 2: Next.js Setup (Week 3)
**Goal**: Frontend project structure

- [ ] Initialize Next.js 15 with App Router
- [ ] Configure Tailwind CSS with DeskCloud theme
- [ ] Install shadcn/ui components
- [ ] Set up environment variables
- [ ] Create API client for backend

**Dependencies**: Phase 1  
**Plan**: `nextjs_landing_dashboard.md` Phase 2

### Phase 3: Landing Page (Week 3-4)
**Goal**: Public marketing site

- [ ] Hero section with Cloud VMs + Connect Agent
- [ ] Features grid
- [ ] Pricing table
- [ ] FAQ section
- [ ] Footer

**Dependencies**: Phase 2  
**Plan**: `nextjs_landing_dashboard.md` Phase 3

### Phase 4: Auth Flow (Week 4)
**Goal**: User authentication

- [ ] Login page
- [ ] Signup page
- [ ] Password reset flow
- [ ] Protected route middleware
- [ ] Cookie handling

**Dependencies**: Phase 1, 2  
**Plan**: `nextjs_landing_dashboard.md` Phase 4

### Phase 5: Dashboard MVP (Weeks 5-6)
**Goal**: Core dashboard functionality

- [ ] Dashboard layout with sidebar
- [ ] Overview page with stats
- [ ] Sessions list page
- [ ] Session detail with VNC viewer
- [ ] API keys management
- [ ] My Devices page (UI only)

**Dependencies**: Phase 4  
**Plan**: `nextjs_landing_dashboard.md` Phase 5

### Phase 6: Connect Agent Core (Weeks 7-10)
**Goal**: Remote agent MVP

- [ ] Python agent with PyAutoGUI
- [ ] Signaling server (device registration)
- [ ] Relay server (WebSocket tunnel)
- [ ] Device claiming flow
- [ ] Session approval popup
- [ ] E2E encryption

**Dependencies**: Phase 5  
**Plan**: `remote_agent_client.md` Phases 1-2

### Phase 7: Connect Agent Packaging (Weeks 11-12)
**Goal**: Cross-platform installers

- [ ] Windows installer (NSIS/MSI)
- [ ] macOS app bundle + notarization
- [ ] Linux packages (deb, AppImage)
- [ ] Dashboard device management integration
- [ ] Always-On / Server Mode

**Dependencies**: Phase 6  
**Plan**: `remote_agent_client.md` Phases 3-4

### Phase 8: Raspberry Pi (Weeks 13-14)
**Goal**: Raspberry Pi emulation

- [ ] QEMU ARM Docker container
- [ ] Display backend abstraction
- [ ] VNC integration
- [ ] GPIO simulation (optional)
- [ ] Dashboard OS selector

**Dependencies**: Phase 5  
**Plan**: `multi_os_support.md` Phase 6

### Phase 9: Video Recording (Weeks 15-17)
**Goal**: Session recording feature

- [ ] FFmpeg recording service
- [ ] Cloudflare R2 storage integration
- [ ] Recording API endpoints
- [ ] Dashboard video player
- [ ] Recording settings UI

**Dependencies**: Phase 5  
**Plan**: `session_video_recording.md`

### Phase 10: Custom Image Builder (Weeks 18-20)
**Goal**: Custom Docker images

- [ ] Image template library
- [ ] Dockerfile generator UI
- [ ] Build worker with BuildKit
- [ ] Image registry integration
- [ ] Dashboard build status

**Dependencies**: Phase 9  
**Plan**: `custom_image_builder.md`

### Future Phases (When Revenue Supports)

- **Android Emulation**: Requires KVM/dedicated servers
- **Windows VMs**: Requires KVM/dedicated servers
- **Enterprise Features**: SSO, SLA, on-premise

---

## Key Decisions Made

### 1. Open Core Model
**Decision**: Open source the MCP core, monetize hosted service + premium features  
**Rationale**: Build community, gain trust, reduce competition threat

### 2. Git Subtree (Not Submodule)
**Decision**: Use git subtree to sync open source core into premium repo  
**Rationale**: Simpler for contributors, no submodule complexity

### 3. SQLModel Over SQLAlchemy
**Decision**: Use SQLModel for all database models  
**Rationale**: Better Pydantic integration, same author as FastAPI

### 4. Vercel Postgres (Not Supabase)
**Decision**: Use Vercel Postgres for shared database  
**Rationale**: Simpler architecture, direct connection from Render.com

### 5. Teal-Forward Branding
**Decision**: Primary color is Teal (#0D9488), not purple  
**Rationale**: Differentiate from purple-heavy AI market (Anthropic, OpenAI)

### 6. Connect Agent on Paid Tiers Only
**Decision**: Remote agent feature requires Pro+ subscription  
**Rationale**: Zero-cost feature for us, high value for users, clear upsell

### 7. Unlimited Remote Sessions
**Decision**: Paid tiers get unlimited remote agent sessions  
**Rationale**: Costs us ~$0.002/session, encourages heavy usage

### 8. Raspberry Pi Before Android
**Decision**: Implement Pi support on Render.com before Android on dedicated servers  
**Rationale**: Cost-efficient, unique market position, no KVM required

### 9. Defer Dedicated Servers Until Revenue
**Decision**: Only add Hetzner/OVH servers when revenue covers 3x cost  
**Rationale**: Stay cost-efficient in early stages

### 10. "Always-On" for Servers
**Decision**: Allow persistent AI access without approval popups  
**Rationale**: Essential for server automation use case

---

## Plan Documents Reference

All detailed planning documents are in `docs/plans/`:

### Premium Features (To Be Implemented)

| Document | Description | Priority |
|----------|-------------|----------|
| **`MASTER_ROADMAP.md`** | This document - project overview | 🔴 Read First |
| **`nextjs_landing_dashboard.md`** | Frontend + auth + dashboard | 🔴 High (Phase 1-5) |
| **`remote_agent_client.md`** | Connect Agent (control your PCs) | 🔴 High (Phase 6-7) |
| **`multi_os_support.md`** | Raspberry Pi, Android, Windows | 🟡 Medium (Phase 8+) |
| **`session_video_recording.md`** | Video recording feature | 🟡 Medium (Phase 9) |
| **`custom_image_builder.md`** | Custom Docker images | 🟢 Low (Phase 10) |

### Core Features (Already Implemented)

| Document | Description | Status |
|----------|-------------|--------|
| **`mcp_server_transformation.md`** | MCP server architecture | ✅ Implemented |
| **`multi_session_scaling.md`** | Multi-display architecture | ✅ Implemented |
| **`session_filesystem_isolation.md`** | OverlayFS isolation | ✅ Implemented |
| **`session_snapshots.md`** | CRIU state persistence | 🔮 Future Research |

### Reading Order for New AI Assistants

1. **This document** (`MASTER_ROADMAP.md`) - Context and overview
2. **`nextjs_landing_dashboard.md`** - Dashboard architecture and auth
3. **`remote_agent_client.md`** - Connect Agent design
4. **Other documents** - As needed for specific features

---

## Infrastructure Strategy

### Current Infrastructure (Render.com)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Current Infrastructure                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Vercel Pro                         Render.com                              │
│  ──────────                         ──────────                              │
│  • Next.js frontend                 • FastAPI backend                       │
│  • Edge functions                   • X11/VNC servers                       │
│  • Vercel Postgres ◄────────────────• Direct DB connection                 │
│                                     • Ubuntu sessions                       │
│                                                                             │
│  Cost: ~$20/mo                      Cost: ~$25-50/mo                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Future Infrastructure (With Dedicated Servers)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Future Infrastructure (When Revenue Allows)               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Vercel Pro          Render.com              Hetzner/OVH                   │
│  ──────────          ──────────              ────────────                   │
│  • Frontend          • Core API              • KVM-enabled                  │
│  • Vercel Postgres   • Ubuntu/Pi VMs         • Android emulation           │
│                      • Connect relay         • Windows VMs                  │
│                                                                             │
│  Trigger: Add dedicated servers only when revenue covers 3x the cost       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Branding & Design

### Brand Identity

| Element | Value |
|---------|-------|
| **Name** | DeskCloud |
| **Tagline** | "AI Agents that Control Any Desktop" |
| **Domains** | deskcloud.app (primary), deskcloud.cc (redirect) |
| **Positioning** | Open source, developer-first, BYOK |

### Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| **Teal** (Primary) | `#0D9488` | CTAs, brand identity |
| **Teal Light** | `#14B8A6` | Hover states, gradients |
| **Sky Blue** | `#0EA5E9` | Links, secondary actions |
| **Amber** | `#F59E0B` | Warnings, premium badges |
| **Violet** | `#8B5CF6` | AI-specific features only |

### Design Principles

1. **Dark Mode First**: 70% of developers prefer dark mode
2. **Teal-Forward**: Differentiate from purple AI companies
3. **Developer-Focused**: Technical, no fluff
4. **Clean & Minimal**: shadcn/ui aesthetic

---

## Getting Started (For New AI Assistants)

### Context You Need

1. **This is the open source repo** - The premium features live in a separate private repo
2. **Planning is complete** - Implementation hasn't started yet
3. **Focus on Phase 1-5 first** - Backend auth, frontend, dashboard
4. **Connect Agent is key** - Major differentiator, implement after dashboard

### Key Files to Know

```
mcp-computer-use/
├── app/
│   ├── api/routes/sessions.py    # Existing session API
│   ├── services/session_manager.py
│   ├── services/display_manager.py
│   └── db/models.py              # Add new models here
├── docs/plans/                    # All planning documents
│   ├── MASTER_ROADMAP.md         # This file
│   ├── nextjs_landing_dashboard.md
│   ├── remote_agent_client.md
│   └── ...
└── README.md                      # Public documentation
```

### When User Asks to "Implement"

1. Read the relevant plan document first
2. Check for dependencies (see roadmap above)
3. Start with the smallest working increment
4. Test locally before suggesting deployment

### Common Tasks

| Task | Relevant Plan |
|------|---------------|
| "Add authentication" | `nextjs_landing_dashboard.md` Phase 1 |
| "Create the landing page" | `nextjs_landing_dashboard.md` Phase 3 |
| "Build the dashboard" | `nextjs_landing_dashboard.md` Phase 5 |
| "Implement Connect Agent" | `remote_agent_client.md` |
| "Add video recording" | `session_video_recording.md` |
| "Add Raspberry Pi" | `multi_os_support.md` |

### Important Constraints

1. **Stay cost-efficient** - Use Render.com/Vercel until revenue justifies more
2. **Open source core** - Don't add premium features to this repo
3. **BYOK model** - Never store Anthropic API keys (use directly)
4. **Security first** - E2E encryption for Connect Agent, session approval required

---

## Appendix: Quick Reference

### Pricing Summary

```
Free:       $0    - 1 VM, Ubuntu only
Pro:        $29   - 5 VMs, 3 devices, Pi, Video, Unlimited remote
Team:       $99   - 20 VMs, 10 devices, Custom images
Enterprise: Custom - Everything
```

### Tech Stack Summary

```
Backend:    FastAPI + SQLModel + PostgreSQL (Render.com)
Frontend:   Next.js 15 + Tailwind + shadcn/ui (Vercel)
Agent:      Python + PyAutoGUI + WebSocket (User's computer)
Database:   Vercel Postgres
Storage:    Cloudflare R2 (videos)
```

### Contact & Resources

- **Domain**: deskcloud.app
- **Open Source**: github.com/[org]/mcp-computer-use
- **MCP Protocol**: https://modelcontextprotocol.io

---

*This document should be read first by any AI assistant working on this project. It provides the complete context needed to continue development.*
