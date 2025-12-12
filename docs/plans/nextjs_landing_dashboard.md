# DeskCloud Next.js Landing Page & Dashboard Plan

> ⚠️ **Start Here**: Read [`MASTER_ROADMAP.md`](./MASTER_ROADMAP.md) first for project context and overview.

> **Domain**: deskcloud.app (primary), deskcloud.cc (redirect)  
> **Frontend**: Vercel Pro  
> **Backend**: Render.com (existing Python/FastAPI)  
> **Created**: December 2025  
> **Priority**: 🔴 High - Implement first

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Tech Stack](#tech-stack)
4. [Phase 1: Backend Auth Infrastructure](#phase-1-backend-auth-infrastructure)
5. [Phase 2: Next.js Project Setup](#phase-2-nextjs-project-setup)
6. [Phase 3: Landing Page](#phase-3-landing-page)
7. [Phase 4: Authentication Flow](#phase-4-authentication-flow)
8. [Phase 5: Dashboard](#phase-5-dashboard)
9. [Phase 6: Integration & Deployment](#phase-6-integration--deployment)
10. [API Specification](#api-specification)
11. [Database Schema](#database-schema)
12. [Security Considerations](#security-considerations)
13. [Timeline & Milestones](#timeline--milestones)

---

## Executive Summary

This plan outlines the development of a professional Next.js frontend for DeskCloud, consisting of:

1. **Landing Page** - Marketing site with features, pricing, and CTAs
2. **Dashboard** - Authenticated area for session management, API keys, and settings
3. **Backend Extensions** - New auth endpoints and user management in the existing FastAPI backend

### Key Objectives

- Create a compelling landing page that converts developers and AI enthusiasts
- Build a functional dashboard for managing AI desktop sessions
- Implement secure authentication with JWT and API key management
- Deploy seamlessly on Vercel with the Python backend on Render.com

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User Browser                                    │
│                                                                             │
│  ┌─────────────────────────────┐    ┌─────────────────────────────────┐    │
│  │   Landing Page (Public)     │    │   Dashboard (Authenticated)     │    │
│  │   - Hero, Features          │    │   - Sessions Management         │    │
│  │   - Pricing, FAQ            │    │   - My Devices (Connect Agent)  │    │
│  │   - Login/Signup            │    │   - API Keys Management         │    │
│  └─────────────────────────────┘    └─────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTPS
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Vercel (deskcloud.app)                              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Next.js 15 (App Router)                           │   │
│  │                                                                       │   │
│  │  ├── app/                                                            │   │
│  │  │   ├── (public)/          # Landing, login, signup                │   │
│  │  │   ├── (dashboard)/       # Protected dashboard routes            │   │
│  │  │   └── api/               # API routes (auth cookies)             │   │
│  │  │                                                                    │   │
│  │  ├── middleware.ts          # Auth protection                        │   │
│  │  └── lib/                   # API client, utils                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTPS + JWT/Cookies
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Render.com (api.deskcloud.app)                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Backend                                    │   │
│  │                                                                       │   │
│  │  ├── /api/v1/auth/*         # New: Authentication endpoints         │   │
│  │  ├── /api/v1/users/*        # New: User management                  │   │
│  │  ├── /api/v1/api-keys/*     # New: API key management              │   │
│  │  ├── /api/v1/sessions/*     # Existing: Session management         │   │
│  │  ├── /mcp                   # Existing: MCP endpoint                │   │
│  │  └── /llms.txt              # Existing: LLM documentation          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                    ┌─────────────────┼─────────────────┐                   │
│                    │                 │                 │                   │
│                    ▼                 ▼                 ▼                   │
│           X11 Displays         VNC Servers        VNC Servers             │
│           (Xvfb per            (VNC per           (noVNC per              │
│            session)             session)           session)               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ DATABASE_URL (connection string)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Vercel Postgres (Shared Database)                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    PostgreSQL Database                                │   │
│  │                                                                       │   │
│  │  Tables:                                                              │   │
│  │  ├── users           # User accounts                                 │   │
│  │  ├── sessions        # AI desktop sessions                           │   │
│  │  ├── messages        # Session messages                              │   │
│  │  ├── api_keys        # User API keys                                 │   │
│  │  └── refresh_tokens  # Auth refresh tokens                           │   │
│  │                                                                       │   │
│  │  Connected via: SQLModel + asyncpg driver                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Frontend (Next.js on Vercel)

| Technology | Purpose | Version |
|------------|---------|---------|
| **Next.js** | React framework with App Router | 15.x |
| **TypeScript** | Type safety | 5.x |
| **Tailwind CSS** | Utility-first styling | 3.x |
| **shadcn/ui** | UI component library | Latest |
| **Lucide React** | Icon library | Latest |
| **React Hook Form** | Form management | 7.x |
| **Zod** | Schema validation | 3.x |
| **SWR / TanStack Query** | Data fetching | Latest |

### Backend Extensions (Python/FastAPI)

| Technology | Purpose | Version |
|------------|---------|---------|
| **SQLModel** | ORM combining SQLAlchemy + Pydantic | 0.0.22+ |
| **python-jose** | JWT encoding/decoding | 3.x |
| **passlib + bcrypt** | Password hashing | Latest |
| **cryptography** | API key encryption | Latest |
| **email-validator** | Email validation | Latest |
| **asyncpg** | Async PostgreSQL driver | Latest |
| **psycopg2-binary** | PostgreSQL adapter (fallback) | Latest |

### Database (Vercel Postgres)

| Component | Details |
|-----------|---------|
| **Provider** | Vercel Postgres (managed PostgreSQL) |
| **Plan** | Included with Vercel Pro |
| **Access** | Connection string (DATABASE_URL) |
| **Consumers** | FastAPI (Render.com) via SQLModel |

> **Note**: Vercel Postgres is a standard PostgreSQL database. The FastAPI backend on Render.com connects using a standard connection string. We use **SQLModel** (by FastAPI's creator) which combines SQLAlchemy core with Pydantic models for seamless FastAPI integration.

### Deployment

| Platform | Purpose | Plan |
|----------|---------|------|
| **Vercel** | Frontend + Database | Pro |
| **Render.com** | Backend (FastAPI) | Existing |

---

## Phase 1: Backend Auth Infrastructure

### 1.1 New Database Models

Add to `app/db/models.py` using **SQLModel**:

```python
# New models using SQLModel (combines SQLAlchemy + Pydantic)

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr
import uuid


def generate_user_uuid() -> str:
    return f"user_{uuid.uuid4().hex[:12]}"


def generate_apikey_uuid() -> str:
    return f"key_{uuid.uuid4().hex[:12]}"


def generate_token_uuid() -> str:
    return f"tok_{uuid.uuid4().hex[:12]}"


class User(SQLModel, table=True):
    """User account for authentication and session ownership."""
    __tablename__ = "users"
    
    id: str = Field(default_factory=generate_user_uuid, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    password_hash: str
    name: Optional[str] = None
    
    # Subscription
    subscription_tier: str = Field(default="free")  # free, pro, team, enterprise
    
    # BYOK - User's own Anthropic API key (encrypted)
    anthropic_api_key_encrypted: Optional[str] = None
    
    # Account status
    email_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Relationships
    sessions: list["Session"] = Relationship(back_populates="user")
    api_keys: list["APIKey"] = Relationship(back_populates="user")
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user")
    devices: list["RemoteDevice"] = Relationship(back_populates="user")


class APIKey(SQLModel, table=True):
    """API keys for programmatic access (MCP, REST API)."""
    __tablename__ = "api_keys"
    
    id: str = Field(default_factory=generate_apikey_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Key identification (prefix shown to user, hash for validation)
    key_prefix: str  # "dk_abc123" (first 8 chars for display)
    key_hash: str    # SHA-256 hash of full key
    
    # Metadata
    name: str  # "Production Key"
    
    # Permissions (stored as JSON string)
    scopes: str = Field(default='["sessions:read","sessions:write","sessions:execute"]')
    
    # Status
    is_active: bool = Field(default=True)
    last_used_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # Optional expiration
    
    # Relationship
    user: Optional["User"] = Relationship(back_populates="api_keys")


class RefreshToken(SQLModel, table=True):
    """Refresh tokens for JWT authentication."""
    __tablename__ = "refresh_tokens"
    
    id: str = Field(default_factory=generate_token_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    token_hash: str
    expires_at: datetime
    
    # Metadata for security
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = None
    
    # Relationship
    user: Optional["User"] = Relationship(back_populates="refresh_tokens")


def generate_device_uuid() -> str:
    return f"dev_{uuid.uuid4().hex[:12]}"


class RemoteDevice(SQLModel, table=True):
    """User's remote device for Connect Agent."""
    __tablename__ = "remote_devices"
    
    id: str = Field(default_factory=generate_device_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Device info
    name: str  # "Work Laptop", "Home Server"
    os_type: str  # "windows", "macos", "linux"
    os_version: Optional[str] = None  # "Windows 11 Pro", "macOS 14.2"
    
    # Agent connection
    public_key: str  # Ed25519 public key for E2E encryption
    claim_token_hash: Optional[str] = None  # Hash of claim token (used during registration)
    
    # Status
    online: bool = Field(default=False)
    last_seen: Optional[datetime] = None
    last_ip: Optional[str] = None
    
    # Always-On / Server Mode
    always_on: bool = Field(default=False)
    always_on_approved_at: Optional[datetime] = None
    
    # Stats
    session_count: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship
    user: Optional["User"] = Relationship(back_populates="devices")


class RemoteSession(SQLModel, table=True):
    """Session record for Connect Agent remote control."""
    __tablename__ = "remote_sessions"
    
    id: str = Field(default_factory=generate_session_uuid, primary_key=True)
    device_id: str = Field(foreign_key="remote_devices.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Session details
    description: Optional[str] = None
    status: str = Field(default="pending")  # pending, approved, active, completed, denied
    
    # Approval
    approved_duration_minutes: Optional[int] = None  # null = forever / always-on
    auto_approved: bool = Field(default=False)  # True if always-on device
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # End reason
    end_reason: Optional[str] = None  # "timeout", "user", "kill_switch", "disconnect"
```

> **Why SQLModel?**
> - Created by FastAPI's author (Sebastián Ramírez)
> - Combines SQLAlchemy (database) + Pydantic (validation) in one class
> - Models work as both database tables AND API request/response schemas
> - Perfect integration with FastAPI's dependency injection

### 1.2 Session Model Updates

Modify existing `Session` model to use **SQLModel** and add user ownership:

```python
# Updated Session model with SQLModel

class Session(SQLModel, table=True):
    """AI desktop session with user ownership."""
    __tablename__ = "sessions"
    
    id: str = Field(default_factory=generate_session_uuid, primary_key=True)
    
    # User ownership (nullable for backward compatibility with existing sessions)
    user_id: Optional[str] = Field(default=None, foreign_key="users.id", index=True)
    
    # Session metadata
    title: Optional[str] = None
    status: str = Field(default="active")  # active, processing, completed, error, archived
    
    # Model configuration
    model: str
    provider: str = Field(default="anthropic")
    system_prompt_suffix: Optional[str] = None
    
    # Display configuration
    display_num: Optional[int] = None
    vnc_port: Optional[int] = None
    novnc_port: Optional[int] = None
    
    # Sharing
    visibility: str = Field(default="private")  # private, shared_link
    share_token: Optional[str] = Field(default=None, unique=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="sessions")
    messages: list["Message"] = Relationship(back_populates="session")
```

> **Migration Note**: Existing sessions will have `user_id=None`. New sessions created through the dashboard will be linked to the authenticated user.

### 1.3 New API Routes Structure

```
app/api/routes/
├── auth.py          # NEW: Authentication endpoints
├── users.py         # NEW: User management
├── api_keys.py      # NEW: API key management
├── sessions.py      # MODIFIED: Add user filtering
├── health.py        # Existing
└── llms.py          # Existing
```

### 1.4 Auth Endpoints

Create `app/api/routes/auth.py`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Create new user account |
| `/api/v1/auth/login` | POST | Authenticate and get tokens |
| `/api/v1/auth/logout` | POST | Revoke refresh token |
| `/api/v1/auth/refresh` | POST | Get new access token |
| `/api/v1/auth/forgot-password` | POST | Request password reset |
| `/api/v1/auth/reset-password` | POST | Reset password with token |
| `/api/v1/auth/verify-email` | POST | Verify email address |

### 1.5 User Endpoints

Create `app/api/routes/users.py`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/users/me` | GET | Get current user profile |
| `/api/v1/users/me` | PATCH | Update user profile |
| `/api/v1/users/me` | DELETE | Delete user account |
| `/api/v1/users/me/password` | PUT | Change password |
| `/api/v1/users/me/api-key` | PUT | Update BYOK Anthropic key |

### 1.6 API Key Endpoints

Create `app/api/routes/api_keys.py`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/api-keys` | GET | List user's API keys |
| `/api/v1/api-keys` | POST | Create new API key |
| `/api/v1/api-keys/{key_id}` | DELETE | Revoke API key |
| `/api/v1/api-keys/{key_id}` | PATCH | Update key name/scopes |

---

## Phase 2: Next.js Project Setup

### 2.1 Initialize Project

```bash
# Create Next.js project
npx create-next-app@latest deskcloud-frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

cd deskcloud-frontend

# Install shadcn/ui
npx shadcn@latest init

# Install additional dependencies
npm install lucide-react @tanstack/react-query zod react-hook-form @hookform/resolvers
npm install jose cookie js-cookie
npm install -D @types/js-cookie
```

### 2.2 Project Structure

```
deskcloud-frontend/
├── src/
│   ├── app/
│   │   ├── (public)/                    # Public routes (no auth required)
│   │   │   ├── page.tsx                 # Landing page (/)
│   │   │   ├── pricing/page.tsx         # Pricing page
│   │   │   ├── login/page.tsx           # Login page
│   │   │   ├── signup/page.tsx          # Signup page
│   │   │   ├── forgot-password/page.tsx
│   │   │   └── reset-password/page.tsx
│   │   │
│   │   ├── (dashboard)/                 # Protected routes
│   │   │   ├── layout.tsx               # Dashboard layout with sidebar
│   │   │   ├── dashboard/
│   │   │   │   ├── page.tsx             # Overview
│   │   │   │   ├── sessions/
│   │   │   │   │   ├── page.tsx         # Session list
│   │   │   │   │   └── [id]/page.tsx    # Session detail
│   │   │   │   ├── api-keys/page.tsx    # API key management
│   │   │   │   └── settings/
│   │   │   │       ├── page.tsx         # General settings
│   │   │   │       ├── profile/page.tsx
│   │   │   │       └── billing/page.tsx
│   │   │
│   │   ├── api/                         # Next.js API routes (for auth cookies)
│   │   │   └── auth/
│   │   │       ├── login/route.ts
│   │   │       ├── logout/route.ts
│   │   │       └── refresh/route.ts
│   │   │
│   │   ├── layout.tsx                   # Root layout
│   │   ├── globals.css                  # Global styles
│   │   └── providers.tsx                # React Query, etc.
│   │
│   ├── components/
│   │   ├── ui/                          # shadcn/ui components
│   │   ├── landing/                     # Landing page components
│   │   │   ├── hero.tsx
│   │   │   ├── features.tsx
│   │   │   ├── pricing.tsx
│   │   │   ├── faq.tsx
│   │   │   └── footer.tsx
│   │   ├── dashboard/                   # Dashboard components
│   │   │   ├── sidebar.tsx
│   │   │   ├── session-card.tsx
│   │   │   ├── api-key-row.tsx
│   │   │   ├── stats-card.tsx
│   │   │   └── vnc-viewer.tsx
│   │   ├── auth/                        # Auth components
│   │   │   ├── login-form.tsx
│   │   │   ├── signup-form.tsx
│   │   │   └── password-reset-form.tsx
│   │   └── common/                      # Shared components
│   │       ├── navbar.tsx
│   │       ├── loading.tsx
│   │       └── error-boundary.tsx
│   │
│   ├── lib/
│   │   ├── api.ts                       # API client for backend
│   │   ├── auth.ts                      # Auth utilities
│   │   ├── utils.ts                     # General utilities
│   │   └── validations.ts               # Zod schemas
│   │
│   ├── hooks/
│   │   ├── use-auth.ts                  # Auth hook
│   │   ├── use-sessions.ts              # Sessions hook
│   │   └── use-api-keys.ts              # API keys hook
│   │
│   ├── types/
│   │   ├── api.ts                       # API response types
│   │   ├── user.ts
│   │   └── session.ts
│   │
│   └── middleware.ts                    # Auth middleware
│
├── public/
│   ├── images/
│   │   ├── logo.svg
│   │   └── hero-screenshot.png
│   └── favicon.ico
│
├── .env.local                           # Local environment
├── .env.example                         # Environment template
├── next.config.js
├── tailwind.config.ts
└── package.json
```

### 2.3 Environment Variables

```bash
# .env.local

# Backend API
NEXT_PUBLIC_API_URL=https://api.deskcloud.app
NEXT_PUBLIC_APP_URL=https://deskcloud.app

# Auth
JWT_SECRET=your-jwt-secret-here
COOKIE_NAME=deskcloud_session

# Analytics (optional)
NEXT_PUBLIC_POSTHOG_KEY=
NEXT_PUBLIC_POSTHOG_HOST=
```

### 2.4 Middleware for Auth Protection

```typescript
// src/middleware.ts
import { NextRequest, NextResponse } from 'next/server'
import { verifyToken } from '@/lib/auth'

const protectedRoutes = ['/dashboard']
const authRoutes = ['/login', '/signup', '/forgot-password', '/reset-password']

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Get token from cookie
  const token = request.cookies.get('deskcloud_session')?.value
  const isAuthenticated = token ? await verifyToken(token) : false
  
  // Redirect unauthenticated users from protected routes
  if (protectedRoutes.some(route => pathname.startsWith(route))) {
    if (!isAuthenticated) {
      const loginUrl = new URL('/login', request.url)
      loginUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(loginUrl)
    }
  }
  
  // Redirect authenticated users from auth routes
  if (authRoutes.includes(pathname)) {
    if (isAuthenticated) {
      return NextResponse.redirect(new URL('/dashboard', request.url))
    }
  }
  
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|images).*)'],
}
```

---

## Phase 3: Landing Page

### 3.1 Page Structure

The landing page will follow this structure:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Navigation Bar                                  │
│  Logo    Features  Pricing  Docs  │  Login  │  Get Started                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                              HERO SECTION                                   │
│                                                                             │
│            AI Agents that Control Any Desktop                               │
│                                                                             │
│     Let Claude browse the web, fill forms, and automate tasks              │
│        on cloud VMs or YOUR OWN computers via MCP                          │
│                                                                             │
│     ☁️ Cloud VMs: Ubuntu • Raspberry Pi • Android (soon)                   │
│     💻 Your Devices: Windows • macOS • Linux                               │
│                                                                             │
│        [ Get Started Free ]    [ View Documentation ]                       │
│                                                                             │
│                     ┌─────────────────────────────┐                        │
│                     │   Hero Screenshot/Video     │                        │
│                     │   (VNC viewer in action)    │                        │
│                     └─────────────────────────────┘                        │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                            FEATURES SECTION                                 │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ ☁️ Cloud    │  │ 💻 Connect  │  │ 🔌 MCP      │  │ 💰 BYOK     │       │
│  │  VMs        │  │  Agent      │  │   Native    │  │   Model     │       │
│  │             │  │   [NEW]     │  │             │  │             │       │
│  │ Ubuntu, Pi  │  │ Control YOUR│  │ Works with  │  │ Use your own│       │
│  │ in cloud    │  │ Windows/Mac │  │ Cursor IDE  │  │ Anthropic   │       │
│  │ sandbox     │  │ Linux PCs   │  │ and Claude  │  │ API key     │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ 🔒 Isolated │  │ 👁️ Live     │  │ 🎬 Video    │  │ 🖥️ Server   │       │
│  │  Sessions   │  │   Viewing   │  │  Recording  │  │   Mode      │       │
│  │             │  │             │  │   [PRO]     │  │             │       │
│  │ Each session│  │ Watch your  │  │ Record for  │  │ 24/7 AI     │       │
│  │ gets its own│  │ agent via   │  │ debugging & │  │ access to   │       │
│  │ filesystem  │  │ VNC         │  │ compliance  │  │ your servers│       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                          HOW IT WORKS                                       │
│                                                                             │
│      1. Create Session  ──▶  2. Execute Task  ──▶  3. Watch Live           │
│                                                                             │
│      Get an isolated         Send instructions     See your AI agent       │
│      virtual desktop         to your AI agent      control the desktop     │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                             PRICING                                         │
│                                                                             │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────────┐           │
│  │   FREE   │  │     PRO      │  │   TEAM   │  │  ENTERPRISE  │           │
│  │   $0     │  │  $29/month   │  │ $99/month│  │   Custom     │           │
│  │          │  │              │  │          │  │              │           │
│  │ 100      │  │ 1,000        │  │ 5,000    │  │ Unlimited    │           │
│  │ sessions │  │ sessions     │  │ sessions │  │ sessions     │           │
│  │          │  │              │  │          │  │              │           │
│  │ BYOK     │  │ + Priority   │  │ + Team   │  │ + SSO        │           │
│  │ only     │  │   support    │  │   mgmt   │  │ + SLA        │           │
│  │          │  │ + Analytics  │  │ + API    │  │ + Dedicated  │           │
│  │          │  │              │  │          │  │              │           │
│  │ [Start]  │  │ [Upgrade]    │  │ [Upgrade]│  │ [Contact]    │           │
│  └──────────┘  └──────────────┘  └──────────┘  └──────────────┘           │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                               FAQ                                           │
│                                                                             │
│  ▸ What is DeskCloud?                                                      │
│  ▸ What is the Connect Agent?                                              │
│  ▸ Is Connect Agent secure?                                                │
│  ▸ What is Server Mode / Always-On?                                        │
│  ▸ Cloud VMs vs Connect Agent - which should I use?                        │
│  ▸ What operating systems are supported?                                   │
│  ▸ How does BYOK work?                                                     │
│  ▸ Can I self-host?                                                        │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                              CTA SECTION                                    │
│                                                                             │
│              Ready to let AI control your virtual desktops?                │
│                                                                             │
│                        [ Get Started Free ]                                 │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                              FOOTER                                         │
│                                                                             │
│  DeskCloud    │  Product     │  Resources   │  Company     │  Legal       │
│  © 2024       │  Features    │  Docs        │  About       │  Privacy     │
│               │  Pricing     │  API         │  Blog        │  Terms       │
│               │  Changelog   │  Status      │  Contact     │              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Hero Component

```tsx
// src/components/landing/hero.tsx
import { Button } from "@/components/ui/button"
import Link from "next/link"

export function Hero() {
  return (
    <section className="relative overflow-hidden py-20 sm:py-32">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-4xl text-center">
          {/* Badge */}
          <div className="mb-8 inline-flex items-center rounded-full border bg-muted px-4 py-1.5 text-sm">
            <span className="mr-2">🚀</span>
            <span>Now with MCP support for Cursor IDE</span>
          </div>
          
          {/* Headline */}
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
            AI Agents that Control{" "}
            <span className="text-primary">Virtual Desktops</span>
          </h1>
          
          {/* Subheadline */}
          <p className="mt-6 text-lg text-muted-foreground sm:text-xl">
            Let Claude browse the web, fill forms, and automate tasks in isolated 
            virtual environments. Connect via MCP from Cursor or Claude Desktop.
          </p>
          
          {/* Two modes: Cloud VMs vs Connect */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
            {/* Cloud VMs */}
            <div className="rounded-lg border bg-muted/50 p-4">
              <div className="text-xs font-semibold text-muted-foreground mb-2">☁️ CLOUD VMs</div>
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center rounded-full bg-orange-500/10 px-2 py-1 text-xs text-orange-500">
                  🐧 Ubuntu
                </span>
                <span className="inline-flex items-center rounded-full bg-pink-500/10 px-2 py-1 text-xs text-pink-500">
                  🍓 Raspberry Pi
                </span>
                <span className="inline-flex items-center rounded-full bg-green-500/10 px-2 py-1 text-xs text-green-500/60">
                  🤖 Android <span className="ml-1 text-[10px]">(soon)</span>
                </span>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">Isolated sandboxes we host</p>
            </div>
            
            {/* Connect Agent */}
            <div className="rounded-lg border border-teal-500/50 bg-teal-500/5 p-4">
              <div className="text-xs font-semibold text-teal-500 mb-2">💻 YOUR DEVICES <span className="ml-1 bg-teal-500 text-white px-1.5 py-0.5 rounded text-[10px]">NEW</span></div>
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center rounded-full bg-blue-500/10 px-2 py-1 text-xs text-blue-500">
                  🪟 Windows
                </span>
                <span className="inline-flex items-center rounded-full bg-gray-500/10 px-2 py-1 text-xs text-gray-400">
                  🍎 macOS
                </span>
                <span className="inline-flex items-center rounded-full bg-orange-500/10 px-2 py-1 text-xs text-orange-500">
                  🐧 Linux
                </span>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">Control your own computers</p>
            </div>
          </div>
          
          {/* CTAs */}
          <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:justify-center">
            <Button size="lg" asChild>
              <Link href="/signup">Get Started Free</Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/docs">View Documentation</Link>
            </Button>
          </div>
          
          {/* Trust badges */}
          <div className="mt-10 flex items-center justify-center gap-8 text-sm text-muted-foreground">
            <span>✓ No credit card required</span>
            <span>✓ BYOK supported</span>
            <span>✓ Open source core</span>
          </div>
        </div>
        
        {/* Hero image */}
        <div className="mt-16">
          <div className="relative mx-auto max-w-5xl rounded-xl border bg-gradient-to-b from-muted/50 to-muted p-2 shadow-2xl">
            <img
              src="/images/hero-screenshot.png"
              alt="DeskCloud dashboard showing AI agent controlling a virtual desktop"
              className="rounded-lg"
            />
          </div>
        </div>
      </div>
    </section>
  )
}
```

### 3.3 Features Data

```typescript
// src/lib/features.ts
import { 
  Cloud,
  Laptop,
  Plug, 
  Key, 
  Shield,
  Eye, 
  Video,
  Server,
  Cpu
} from "lucide-react"

export const features = [
  // Primary features (top row)
  {
    icon: Cloud,
    title: "Cloud VMs",
    description: "Isolated Ubuntu and Raspberry Pi virtual machines we host. Perfect for testing, demos, and untrusted automation.",
  },
  {
    icon: Laptop,
    title: "Connect Agent",
    description: "Install our lightweight agent on YOUR Windows, macOS, or Linux computer. Let AI control your real apps like Outlook, SAP, and more.",
    badge: "NEW",
    highlight: true,
  },
  {
    icon: Plug,
    title: "MCP Native",
    description: "First-class Model Context Protocol support. Works seamlessly with Cursor IDE and Claude Desktop.",
  },
  {
    icon: Key,
    title: "BYOK Model",
    description: "Bring Your Own Key. Use your Anthropic API key and pay only for what you use. We charge for infrastructure, not AI.",
  },
  // Secondary features (bottom row)
  {
    icon: Shield,
    title: "Secure by Design",
    description: "E2E encryption, session approval popups, and kill switch. You're always in control of what AI can access.",
  },
  {
    icon: Eye,
    title: "Live Viewing",
    description: "Watch your AI agent in real-time via VNC. See exactly what Claude sees and does on the desktop.",
  },
  {
    icon: Video,
    title: "Session Recording",
    description: "Record your AI agent sessions as video. Perfect for debugging, compliance, and creating training content.",
    badge: "PRO",
  },
  {
    icon: Server,
    title: "Server Mode",
    description: "Grant 24/7 'Always-On' access for servers and headless machines. Perfect for automation that runs while you sleep.",
    badge: "PRO",
  },
  {
    icon: Cpu,
    title: "Raspberry Pi",
    description: "Unique in the market! Run AI agents on emulated Raspberry Pi. Perfect for IoT development and home automation.",
    badge: "UNIQUE",
  },
]
```

### 3.4 Pricing Data

```typescript
// src/lib/pricing.ts
export const pricingTiers = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Perfect for getting started",
    features: [
      "1 concurrent cloud session",
      "Ubuntu Linux VMs only",
      "24-hour session history",
      "BYOK (your API key)",
      "Community support",
    ],
    notIncluded: [
      "Connect Agent (your devices)",
      "Video recording",
    ],
    cta: "Get Started",
    href: "/signup",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For individual developers",
    features: [
      "5 concurrent cloud sessions",
      "Ubuntu + Raspberry Pi 🍓",
      "Connect Agent: 3 devices 💻",
      "Unlimited remote sessions ∞",
      "Server Mode (Always-On) 🖥️",
      "Video recording 🎬",
      "30-day session history",
      "Priority email support",
    ],
    cta: "Start Pro Trial",
    href: "/signup?plan=pro",
    highlighted: true,
  },
  {
    name: "Team",
    price: "$99",
    period: "/month",
    description: "For growing teams",
    features: [
      "20 concurrent cloud sessions",
      "Ubuntu + Raspberry Pi 🍓",
      "Connect Agent: 10 devices 💻",
      "Unlimited remote sessions ∞",
      "Server Mode (Always-On) 🖥️",
      "Video recording 🎬",
      "Custom image builder 🐳",
      "90-day session history",
      "Team management",
      "Priority support",
    ],
    cta: "Start Team Trial",
    href: "/signup?plan=team",
    highlighted: false,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    description: "For large organizations",
    features: [
      "Unlimited cloud sessions",
      "All Cloud OS (Ubuntu, Pi, Android)",
      "Connect Agent: Unlimited 💻",
      "Unlimited remote sessions ∞",
      "Server Mode (Always-On) 🖥️",
      "Video recording 🎬",
      "Custom images + BYOI 🐳",
      "Unlimited history",
      "SSO/SAML",
      "SLA guarantee",
      "On-premise relay server",
    ],
    cta: "Contact Sales",
    href: "/contact",
    highlighted: false,
  },
]
```

### 3.5 FAQ Data

```typescript
// src/lib/faq.ts
export const faqItems = [
  {
    question: "What is DeskCloud?",
    answer: "DeskCloud lets AI agents control computers via MCP. We offer two modes: Cloud VMs (isolated Ubuntu/Raspberry Pi sandboxes we host) and Connect Agent (control your own Windows, macOS, or Linux computers).",
  },
  {
    question: "What is the Connect Agent?",
    answer: "Connect Agent is a lightweight app you install on your own Windows, macOS, or Linux computer. Once installed, AI agents can control that computer remotely - automating real apps like Outlook, SAP, Salesforce, and more. Available on Pro, Team, and Enterprise plans.",
  },
  {
    question: "Is Connect Agent secure?",
    answer: "Yes! Connect Agent uses end-to-end encryption, requires session approval before AI can control (popup with time limits), and has a kill switch (Ctrl+Alt+Esc). Only your account can control your claimed devices. For servers, you can enable 'Always-On' mode with one-click revocation.",
  },
  {
    question: "What is Server Mode / Always-On?",
    answer: "Server Mode lets you grant persistent AI access without approval popups - perfect for headless servers, home labs, and CI/CD machines. Sessions are auto-approved 24/7 until you revoke. You can revoke instantly from the system tray or dashboard.",
  },
  {
    question: "Cloud VMs vs Connect Agent - which should I use?",
    answer: "Use Cloud VMs for testing, demos, and untrusted automation (isolated sandbox). Use Connect Agent when you need AI to access your real apps, files, and hardware (Windows Outlook, SAP, printers, etc.).",
  },
  {
    question: "What operating systems are supported?",
    answer: "Cloud VMs: Ubuntu Linux and Raspberry Pi OS (Android coming soon). Connect Agent: Windows, macOS, and Linux. Each runs in isolation that your AI agent can fully control.",
  },
  {
    question: "What can I do with Raspberry Pi support?",
    answer: "Our Raspberry Pi support is unique in the market! You can develop and test IoT applications, automate home automation setups, test GPIO interactions, and run embedded system workflows - all without physical hardware.",
  },
  {
    question: "How does BYOK (Bring Your Own Key) work?",
    answer: "You provide your own Anthropic API key. DeskCloud only charges for infrastructure, not for AI usage. This means transparent pricing - you see exactly what you pay for AI separately from infrastructure.",
  },
  {
    question: "What is MCP (Model Context Protocol)?",
    answer: "MCP is an open protocol by Anthropic that allows AI assistants to securely connect to external tools. DeskCloud implements MCP to let Claude control desktops directly from Cursor IDE or Claude Desktop.",
  },
  {
    question: "Is my data secure?",
    answer: "Yes. Cloud VMs use filesystem isolation (OverlayFS) and are cleaned up automatically. Connect Agent uses E2E encryption - even our relay servers can't see your screen or commands. We don't store your Anthropic API key.",
  },
  {
    question: "Can I self-host DeskCloud?",
    answer: "Yes! Our core is open source (MIT licensed). You can self-host the Cloud VM platform for free. Connect Agent relay servers can also be self-hosted on Enterprise plans.",
  },
]
```

---

## Phase 4: Authentication Flow

### 4.1 Auth Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SIGNUP FLOW                                       │
│                                                                             │
│  User fills form ──▶ POST /api/v1/auth/register ──▶ Create user            │
│                              │                           │                  │
│                              ▼                           ▼                  │
│                      Validate email/pw           Hash password              │
│                              │                           │                  │
│                              ▼                           ▼                  │
│                      Return JWT tokens ◀──────── Store in DB               │
│                              │                                              │
│                              ▼                                              │
│                      Set HttpOnly cookie                                    │
│                              │                                              │
│                              ▼                                              │
│                      Redirect to /dashboard                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            LOGIN FLOW                                        │
│                                                                             │
│  User fills form ──▶ POST /api/v1/auth/login ──▶ Verify credentials        │
│                              │                           │                  │
│                              ▼                           ▼                  │
│                      Validate email/pw           Check password hash        │
│                              │                           │                  │
│                              ▼                           ▼                  │
│                      Return JWT tokens ◀──────── Generate tokens           │
│                              │                                              │
│                              ▼                                              │
│                      Set HttpOnly cookie                                    │
│                              │                                              │
│                              ▼                                              │
│                      Redirect to /dashboard                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          TOKEN REFRESH FLOW                                  │
│                                                                             │
│  Access token expires ──▶ Middleware detects ──▶ Check refresh token       │
│                                  │                        │                 │
│                                  ▼                        ▼                 │
│                           POST /api/v1/auth/refresh       │                 │
│                                  │                        │                 │
│                                  ▼                        ▼                 │
│                           New access token ◀────── Validate refresh        │
│                                  │                                          │
│                                  ▼                                          │
│                           Update cookie                                     │
│                                  │                                          │
│                                  ▼                                          │
│                           Continue request                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 JWT Token Structure

```json
// Access Token (15 min expiry)
{
  "sub": "user_abc123",           // User ID
  "email": "user@example.com",
  "tier": "pro",                  // Subscription tier
  "iat": 1702234567,              // Issued at
  "exp": 1702235467,              // Expires at
  "type": "access"
}

// Refresh Token (7 day expiry)
{
  "sub": "user_abc123",
  "jti": "token_xyz789",          // Token ID (for revocation)
  "iat": 1702234567,
  "exp": 1702839367,
  "type": "refresh"
}
```

### 4.3 Login Form Component

```tsx
// src/components/auth/login-form.tsx
"use client"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Icons } from "@/components/icons"
import Link from "next/link"

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
})

type LoginFormData = z.infer<typeof loginSchema>

export function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const redirect = searchParams.get("redirect") || "/dashboard"
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  })

  async function onSubmit(data: LoginFormData) {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.message || "Login failed")
      }

      router.push(redirect)
      router.refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
      {error && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="you@example.com"
          {...form.register("email")}
        />
        {form.formState.errors.email && (
          <p className="text-sm text-destructive">
            {form.formState.errors.email.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="password">Password</Label>
          <Link
            href="/forgot-password"
            className="text-sm text-muted-foreground hover:text-primary"
          >
            Forgot password?
          </Link>
        </div>
        <Input
          id="password"
          type="password"
          {...form.register("password")}
        />
        {form.formState.errors.password && (
          <p className="text-sm text-destructive">
            {form.formState.errors.password.message}
          </p>
        )}
      </div>

      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading && <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />}
        Sign In
      </Button>

      <p className="text-center text-sm text-muted-foreground">
        Don't have an account?{" "}
        <Link href="/signup" className="text-primary hover:underline">
          Sign up
        </Link>
      </p>
    </form>
  )
}
```

---

## Phase 5: Dashboard

### 5.1 Dashboard Layout

```tsx
// src/app/(dashboard)/layout.tsx
import { AppSidebar } from "@/components/dashboard/sidebar"
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { getUser } from "@/lib/auth"
import { redirect } from "next/navigation"

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const user = await getUser()
  
  if (!user) {
    redirect("/login")
  }

  return (
    <SidebarProvider>
      <AppSidebar user={user} />
      <SidebarInset>
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
```

### 5.2 Dashboard Sidebar

```tsx
// src/components/dashboard/sidebar.tsx
"use client"

import {
  LayoutDashboard,
  Monitor,
  Laptop,
  Key,
  Settings,
  HelpCircle,
  LogOut,
} from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import Link from "next/link"
import { usePathname } from "next/navigation"
import type { User } from "@/types/user"

const menuItems = [
  { title: "Overview", url: "/dashboard", icon: LayoutDashboard },
  { title: "Sessions", url: "/dashboard/sessions", icon: Monitor },
  { title: "My Devices", url: "/dashboard/devices", icon: Laptop, badge: "NEW" },
  { title: "API Keys", url: "/dashboard/api-keys", icon: Key },
  { title: "Settings", url: "/dashboard/settings", icon: Settings },
]

export function AppSidebar({ user }: { user: User }) {
  const pathname = usePathname()

  return (
    <Sidebar>
      <SidebarHeader className="border-b px-6 py-4">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            DC
          </div>
          <span className="font-semibold">DeskCloud</span>
        </Link>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Menu</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={pathname === item.url}
                  >
                    <Link href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Support</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <Link href="/docs">
                    <HelpCircle className="h-4 w-4" />
                    <span>Documentation</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t p-4">
        <div className="flex items-center gap-3">
          <Avatar className="h-9 w-9">
            <AvatarFallback>
              {user.name?.charAt(0) || user.email.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 overflow-hidden">
            <p className="truncate text-sm font-medium">{user.name || "User"}</p>
            <p className="truncate text-xs text-muted-foreground">{user.email}</p>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
```

### 5.3 Dashboard Pages Overview

| Page | Route | Purpose |
|------|-------|---------|
| **Overview** | `/dashboard` | Stats cards, recent sessions, quick actions |
| **Sessions** | `/dashboard/sessions` | List all sessions, create new, filter/search |
| **Session Detail** | `/dashboard/sessions/[id]` | View session, VNC viewer, message history |
| **API Keys** | `/dashboard/api-keys` | List, create, delete API keys |
| **Settings** | `/dashboard/settings` | General account settings |
| **Profile** | `/dashboard/settings/profile` | Update name, email, password |
| **Billing** | `/dashboard/settings/billing` | Subscription management (future) |

### 5.4 Sessions Page

```tsx
// src/app/(dashboard)/dashboard/sessions/page.tsx
import { Suspense } from "react"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { SessionList } from "@/components/dashboard/session-list"
import { CreateSessionDialog } from "@/components/dashboard/create-session-dialog"

export default function SessionsPage() {
  return (
    <div className="container py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sessions</h1>
          <p className="text-muted-foreground">
            Manage your AI desktop sessions
          </p>
        </div>
        <CreateSessionDialog>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Session
          </Button>
        </CreateSessionDialog>
      </div>

      <Suspense fallback={<SessionListSkeleton />}>
        <SessionList />
      </Suspense>
    </div>
  )
}
```

### 5.5 My Devices Page (Connect Agent)

```tsx
// src/app/(dashboard)/dashboard/devices/page.tsx
import { Suspense } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Plus, Download, Laptop, Server } from "lucide-react"
import { DeviceList } from "@/components/dashboard/device-list"
import { DeviceListSkeleton } from "@/components/dashboard/device-list-skeleton"

export default function DevicesPage() {
  return (
    <div className="container py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            My Devices
            <Badge variant="secondary">NEW</Badge>
          </h1>
          <p className="text-muted-foreground">
            Connect your own computers for AI control
          </p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Add Device
        </Button>
      </div>

      {/* How it works banner */}
      <div className="mb-6 rounded-lg border border-teal-500/50 bg-teal-500/5 p-4">
        <h3 className="font-semibold text-teal-500 mb-2">How Connect Agent Works</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
          <div className="flex items-start gap-2">
            <Download className="w-5 h-5 text-teal-500 shrink-0" />
            <span>1. Download & install the Connect Agent on your Windows, macOS, or Linux computer</span>
          </div>
          <div className="flex items-start gap-2">
            <Laptop className="w-5 h-5 text-teal-500 shrink-0" />
            <span>2. Your device appears here. Start AI sessions that control your real computer</span>
          </div>
          <div className="flex items-start gap-2">
            <Server className="w-5 h-5 text-teal-500 shrink-0" />
            <span>3. Enable "Always-On" for servers to allow 24/7 AI access without popups</span>
          </div>
        </div>
      </div>

      <Suspense fallback={<DeviceListSkeleton />}>
        <DeviceList />
      </Suspense>
    </div>
  )
}
```

### 5.6 Device List Component

```tsx
// src/components/dashboard/device-list.tsx
"use client"

import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { 
  Laptop, 
  Monitor, 
  Server,
  MoreVertical,
  Play,
  History,
  Settings,
  Trash2,
  Shield,
  ShieldOff
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface Device {
  id: string
  name: string
  os: "windows" | "macos" | "linux"
  online: boolean
  alwaysOn: boolean
  lastActive: string
  sessionCount: number
}

const osIcons = {
  windows: "🪟",
  macos: "🍎",
  linux: "🐧",
}

export function DeviceList() {
  const { data: devices, isLoading } = useQuery({
    queryKey: ["devices"],
    queryFn: () => fetch("/api/devices").then(res => res.json()),
  })

  if (isLoading) return <DeviceListSkeleton />
  if (!devices?.length) return <EmptyDeviceState />

  return (
    <div className="grid gap-4">
      {devices.map((device: Device) => (
        <Card key={device.id} className={device.alwaysOn ? "border-purple-500/50" : ""}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{osIcons[device.os]}</span>
                <div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    {device.name}
                    {device.online ? (
                      <span className="h-2 w-2 rounded-full bg-green-500" />
                    ) : (
                      <span className="h-2 w-2 rounded-full bg-gray-400" />
                    )}
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">
                    {device.os === "windows" && "Windows"}
                    {device.os === "macos" && "macOS"}
                    {device.os === "linux" && "Linux"}
                    {" • "}
                    {device.online ? "Online" : `Last seen ${device.lastActive}`}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                {device.alwaysOn && (
                  <Badge variant="outline" className="border-purple-500 text-purple-500">
                    <Server className="w-3 h-3 mr-1" />
                    Always-On
                  </Badge>
                )}
                
                <Button 
                  size="sm" 
                  disabled={!device.online}
                >
                  <Play className="w-4 h-4 mr-1" />
                  Start Session
                </Button>
                
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>
                      <History className="w-4 h-4 mr-2" />
                      View History
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Settings className="w-4 h-4 mr-2" />
                      Settings
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    {device.alwaysOn ? (
                      <DropdownMenuItem className="text-orange-500">
                        <ShieldOff className="w-4 h-4 mr-2" />
                        Revoke Always-On
                      </DropdownMenuItem>
                    ) : (
                      <DropdownMenuItem className="text-purple-500">
                        <Shield className="w-4 h-4 mr-2" />
                        Enable Always-On
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem className="text-destructive">
                      <Trash2 className="w-4 h-4 mr-2" />
                      Remove Device
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {device.sessionCount} sessions • Device ID: {device.id}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function EmptyDeviceState() {
  return (
    <Card className="p-8 text-center">
      <Laptop className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
      <h3 className="text-lg font-semibold mb-2">No devices connected</h3>
      <p className="text-muted-foreground mb-4">
        Download the Connect Agent to control your own Windows, macOS, or Linux computer with AI.
      </p>
      <Button>
        <Plus className="w-4 h-4 mr-2" />
        Add Your First Device
      </Button>
    </Card>
  )
}
```

### 5.7 VNC Viewer Component

```tsx
// src/components/dashboard/vnc-viewer.tsx
"use client"

import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Maximize2, Minimize2, RefreshCw } from "lucide-react"

interface VNCViewerProps {
  sessionId: string
  vncUrl: string
}

export function VNCViewer({ sessionId, vncUrl }: VNCViewerProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isConnected, setIsConnected] = useState(true)

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      iframeRef.current?.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  const refresh = () => {
    if (iframeRef.current) {
      iframeRef.current.src = iframeRef.current.src
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <CardTitle className="text-sm font-medium">Virtual Desktop</CardTitle>
          <Badge variant={isConnected ? "default" : "destructive"}>
            {isConnected ? "Connected" : "Disconnected"}
          </Badge>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" onClick={refresh}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={toggleFullscreen}>
            {isFullscreen ? (
              <Minimize2 className="h-4 w-4" />
            ) : (
              <Maximize2 className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative aspect-video overflow-hidden rounded-lg border bg-black">
          <iframe
            ref={iframeRef}
            src={vncUrl}
            className="h-full w-full"
            allow="clipboard-read; clipboard-write"
          />
        </div>
      </CardContent>
    </Card>
  )
}
```

---

## Phase 6: Integration & Deployment

### 6.1 API Client

```typescript
// src/lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL

interface RequestOptions extends RequestInit {
  params?: Record<string, string>
}

class APIClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, ...fetchOptions } = options
    
    let url = `${this.baseUrl}${endpoint}`
    if (params) {
      const searchParams = new URLSearchParams(params)
      url += `?${searchParams.toString()}`
    }

    const response = await fetch(url, {
      ...fetchOptions,
      headers: {
        "Content-Type": "application/json",
        ...fetchOptions.headers,
      },
      credentials: "include", // Include cookies for auth
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new APIError(error.detail || "Request failed", response.status)
    }

    return response.json()
  }

  // Auth endpoints
  async login(email: string, password: string) {
    return this.request("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
  }

  async register(email: string, password: string, name?: string) {
    return this.request("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    })
  }

  // Session endpoints
  async getSessions(params?: { limit?: number; offset?: number }) {
    return this.request<SessionListResponse>("/api/v1/sessions", { params })
  }

  async getSession(id: string) {
    return this.request<Session>(`/api/v1/sessions/${id}`)
  }

  async createSession(data: CreateSessionRequest) {
    return this.request<Session>("/api/v1/sessions", {
      method: "POST",
      body: JSON.stringify(data),
    })
  }

  async deleteSession(id: string) {
    return this.request(`/api/v1/sessions/${id}`, { method: "DELETE" })
  }

  // API Key endpoints
  async getAPIKeys() {
    return this.request<APIKey[]>("/api/v1/api-keys")
  }

  async createAPIKey(name: string, scopes?: string[]) {
    return this.request<{ key: string; apiKey: APIKey }>("/api/v1/api-keys", {
      method: "POST",
      body: JSON.stringify({ name, scopes }),
    })
  }

  async deleteAPIKey(id: string) {
    return this.request(`/api/v1/api-keys/${id}`, { method: "DELETE" })
  }
}

class APIError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
    this.name = "APIError"
  }
}

export const api = new APIClient(API_URL!)
```

### 6.2 CORS Configuration (Backend)

Update `app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

# Production CORS origins
CORS_ORIGINS = [
    "https://deskcloud.app",
    "https://www.deskcloud.app",
    "https://deskcloud.cc",
    "http://localhost:3000",  # Development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,  # Required for cookies
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],  # For pagination
)
```

### 6.3 Vercel Configuration

```json
// vercel.json
{
  "framework": "nextjs",
  "regions": ["iad1"],  // US East (close to Render)
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        }
      ]
    }
  ],
  "rewrites": [
    {
      "source": "/api/backend/:path*",
      "destination": "https://api.deskcloud.app/api/v1/:path*"
    }
  ]
}
```

### 6.4 Environment Variables (Vercel)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL (https://api.deskcloud.app) |
| `NEXT_PUBLIC_APP_URL` | Frontend URL (https://deskcloud.app) |
| `JWT_SECRET` | Secret for JWT verification |
| `COOKIE_DOMAIN` | Cookie domain (.deskcloud.app) |

### 6.5 Domain Setup

1. **Vercel**:
   - Add `deskcloud.app` as production domain
   - Add `deskcloud.cc` as redirect to `.app`
   - Configure SSL (automatic)

2. **Render.com**:
   - Add `api.deskcloud.app` as custom domain
   - Configure SSL (automatic)

3. **DNS Records**:
   ```
   deskcloud.app        A     76.76.21.21 (Vercel)
   www.deskcloud.app    CNAME cname.vercel-dns.com
   deskcloud.cc         A     76.76.21.21 (redirect)
   api.deskcloud.app    CNAME your-app.onrender.com
   ```

---

## API Specification

### Authentication Endpoints

#### POST /api/v1/auth/register

```json
// Request
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}

// Response 201
{
  "user": {
    "id": "user_abc123",
    "email": "user@example.com",
    "name": "John Doe",
    "subscription_tier": "free",
    "created_at": "2024-12-10T10:00:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

#### POST /api/v1/auth/login

```json
// Request
{
  "email": "user@example.com",
  "password": "securepassword123"
}

// Response 200
{
  "user": { ... },
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "Bearer",
  "expires_in": 900
}

// Response 401
{
  "detail": "Invalid email or password"
}
```

#### POST /api/v1/auth/refresh

```json
// Request
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}

// Response 200
{
  "access_token": "...",
  "expires_in": 900
}
```

### API Key Endpoints

#### POST /api/v1/api-keys

```json
// Request
{
  "name": "Production Key",
  "scopes": ["sessions:read", "sessions:write", "sessions:execute"]
}

// Response 201
{
  "key": "dk_abc123xyz789...",  // Only shown once!
  "api_key": {
    "id": "key_def456",
    "name": "Production Key",
    "key_prefix": "dk_abc123",
    "scopes": ["sessions:read", "sessions:write", "sessions:execute"],
    "created_at": "2024-12-10T10:00:00Z",
    "last_used_at": null
  }
}
```

### Device Endpoints (Connect Agent)

#### GET /api/v1/devices

List all devices for the authenticated user.

```json
// Response 200
{
  "devices": [
    {
      "id": "dev_abc123",
      "name": "Work Laptop",
      "os_type": "windows",
      "os_version": "Windows 11 Pro",
      "online": true,
      "last_seen": "2024-12-10T10:30:00Z",
      "always_on": false,
      "session_count": 47,
      "created_at": "2024-12-01T09:00:00Z"
    },
    {
      "id": "dev_xyz789",
      "name": "Home Server",
      "os_type": "linux",
      "os_version": "Ubuntu 24.04 LTS",
      "online": true,
      "last_seen": "2024-12-10T10:35:00Z",
      "always_on": true,
      "always_on_approved_at": "2024-12-05T14:00:00Z",
      "session_count": 847,
      "created_at": "2024-12-05T14:00:00Z"
    }
  ]
}
```

#### POST /api/v1/devices/claim-token

Generate a claim token for a new device. Token is embedded in the installer download.

```json
// Request
{
  "name": "My New Laptop"
}

// Response 201
{
  "claim_token": "clm_abc123xyz789...",  // One-time use
  "expires_at": "2024-12-10T11:00:00Z",  // 1 hour expiry
  "download_urls": {
    "windows": "https://deskcloud.app/download/connect/windows?token=clm_abc123xyz789",
    "macos": "https://deskcloud.app/download/connect/macos?token=clm_abc123xyz789",
    "linux": "https://deskcloud.app/download/connect/linux?token=clm_abc123xyz789"
  }
}
```

#### PATCH /api/v1/devices/:id

Update device settings.

```json
// Request
{
  "name": "Updated Device Name",
  "always_on": true
}

// Response 200
{
  "device": {
    "id": "dev_abc123",
    "name": "Updated Device Name",
    "always_on": true,
    "always_on_approved_at": "2024-12-10T10:40:00Z"
    // ... other fields
  }
}
```

#### DELETE /api/v1/devices/:id

Remove a device. Also revokes all active sessions.

```json
// Response 204 (No Content)
```

#### POST /api/v1/devices/:id/sessions

Start a remote control session on a device.

```json
// Request
{
  "description": "Help organize my Downloads folder"
}

// Response 201
{
  "session_id": "rsess_abc123",
  "status": "pending",  // Waiting for user approval (or "approved" if always_on)
  "device": {
    "id": "dev_abc123",
    "name": "Work Laptop",
    "online": true
  }
}

// Response 400 (Device offline)
{
  "detail": "Device is offline"
}
```

#### GET /api/v1/devices/:id/sessions

Get session history for a device.

```json
// Response 200
{
  "sessions": [
    {
      "id": "rsess_abc123",
      "description": "Organize Downloads folder",
      "status": "completed",
      "auto_approved": false,
      "approved_duration_minutes": 30,
      "created_at": "2024-12-10T09:00:00Z",
      "started_at": "2024-12-10T09:00:30Z",
      "ended_at": "2024-12-10T09:25:00Z",
      "end_reason": "user"
    }
  ],
  "total": 47,
  "page": 1,
  "per_page": 20
}
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     users       │       │    sessions     │       │    messages     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id          PK  │──┐    │ id          PK  │──┐    │ id          PK  │
│ email           │  │    │ user_id     FK  │◀─┘    │ session_id  FK  │◀─┐
│ password_hash   │  │    │ title           │       │ role            │  │
│ name            │  │    │ status          │       │ content         │  │
│ subscription_   │  │    │ model           │       │ tool_use_id     │  │
│   tier          │  │    │ provider        │       │ created_at      │  │
│ anthropic_api_  │  │    │ display_num     │       └─────────────────┘  │
│   key_encrypted │  │    │ vnc_port        │                            │
│ email_verified  │  │    │ novnc_port      │                            │
│ is_active       │  │    │ visibility      │                            │
│ created_at      │  │    │ share_token     │                            │
│ updated_at      │  │    │ created_at      │                            │
│ last_login      │  │    │ updated_at      │                            │
└─────────────────┘  │    │ last_activity   │                            │
         │           │    └─────────────────┘                            │
         │           │              │                                    │
         │           └──────────────┼────────────────────────────────────┘
         │                          │
         │    ┌─────────────────┐   │    ┌─────────────────┐
         │    │    api_keys     │   │    │ refresh_tokens  │
         │    ├─────────────────┤   │    ├─────────────────┤
         ├───▶│ id          PK  │   │    │ id          PK  │
         │    │ user_id     FK  │◀──┘    │ user_id     FK  │◀─┐
         │    │ key_prefix      │        │ token_hash      │  │
         │    │ key_hash        │        │ expires_at      │  │
         │    │ name            │        │ ip_address      │  │
         │    │ scopes          │        │ user_agent      │  │
         │    │ is_active       │        │ created_at      │  │
         │    │ created_at      │        │ revoked_at      │  │
         │    └─────────────────┘        └─────────────────┘  │
         │                                                     │
         │    ┌─────────────────┐        ┌─────────────────┐  │
         │    │ remote_devices  │        │ remote_sessions │  │
         │    ├─────────────────┤        ├─────────────────┤  │
         ├───▶│ id          PK  │──┐     │ id          PK  │  │
         │    │ user_id     FK  │◀─┘     │ device_id   FK  │◀─┤
         │    │ name            │        │ user_id     FK  │◀─┘
         │    │ os_type         │        │ description     │
         │    │ os_version      │        │ status          │
         │    │ public_key      │        │ auto_approved   │
         │    │ online          │        │ approved_dur... │
         │    │ always_on       │        │ created_at      │
         │    │ session_count   │        │ started_at      │
         │    │ created_at      │        │ ended_at        │
         │    └─────────────────┘        └─────────────────┘
         │    │ name            │        │ ip_address      │  │
         │    │ scopes          │        │ user_agent      │  │
         │    │ is_active       │        │ created_at      │  │
         │    │ last_used_at    │        │ revoked_at      │  │
         │    │ created_at      │        └─────────────────┘  │
         │    │ expires_at      │                             │
         │    └─────────────────┘                             │
         │                                                    │
         └────────────────────────────────────────────────────┘
```

---

## Security Considerations

### Password Security
- Hash with bcrypt (cost factor 12)
- Minimum 8 characters
- Check against common password lists

### JWT Security
- Access tokens: 15 minute expiry
- Refresh tokens: 7 day expiry
- Stored in HttpOnly, Secure, SameSite=Lax cookies
- Rotate refresh tokens on use

### API Key Security
- Generate 32 random bytes (256 bits)
- Show full key only once on creation
- Store SHA-256 hash
- Prefix for identification (dk_xxxxx)

### Rate Limiting
```python
# Suggested limits
"/api/v1/auth/login": "5/minute"
"/api/v1/auth/register": "3/minute"
"/api/v1/auth/forgot-password": "3/minute"
"/api/v1/sessions": "100/minute"
"/api/v1/api-keys": "20/minute"
```

### CORS
- Strict origin list (no wildcards in production)
- Credentials enabled for cookie auth
- Preflight caching (24 hours)

---

## Timeline & Milestones

### Phase 1: Backend Auth (Week 1-2)
- [ ] User model and migrations
- [ ] Auth endpoints (register, login, logout, refresh)
- [ ] API key management
- [ ] Session filtering by user
- [ ] CORS configuration

### Phase 2: Next.js Setup (Week 2)
- [ ] Project initialization
- [ ] shadcn/ui setup
- [ ] Project structure
- [ ] Environment configuration

### Phase 3: Landing Page (Week 3)
- [ ] Hero section
- [ ] Features section
- [ ] Pricing section
- [ ] FAQ section
- [ ] Footer
- [ ] Mobile responsiveness

### Phase 4: Auth Flow (Week 3-4)
- [ ] Login page
- [ ] Signup page
- [ ] Password reset flow
- [ ] Middleware protection
- [ ] Cookie handling

### Phase 5: Dashboard (Week 4-5)
- [ ] Dashboard layout with sidebar
- [ ] Overview page with stats
- [ ] Sessions list page
- [ ] Session detail with VNC viewer
- [ ] My Devices page (Connect Agent)
- [ ] Add Device flow with download links
- [ ] Device settings & Always-On toggle
- [ ] API keys management page
- [ ] Settings page

### Phase 6: Integration & Launch (Week 5-6)
- [ ] API client integration
- [ ] Error handling
- [ ] Loading states
- [ ] Vercel deployment
- [ ] Domain configuration
- [ ] Testing & bug fixes

---

## Next Steps

1. **Start with backend auth** - This unblocks the frontend work
2. **Create Next.js project** - Set up the foundation
3. **Build landing page first** - Can deploy immediately for marketing
4. **Implement auth flow** - Enable user registration
5. **Build dashboard** - Core functionality
6. **Deploy and iterate** - Launch MVP, gather feedback

---

## Brand Identity & Visual Guidelines

### Brand Positioning

**DeskCloud** should evoke:
- 🔮 **Innovation** - Cutting-edge AI technology
- 🛡️ **Trust** - Enterprise-grade security and reliability
- ⚡ **Power** - Full control over virtual environments
- 🎯 **Simplicity** - Complex tech made accessible

**Target Emotions**: Excitement, confidence, empowerment, curiosity

---

### Color Palette (2025-2026 Validated)

> **Research-Based**: This palette is validated against 2025-2026 design trends including:
> - Pantone 2025 "Mocha Mousse" (warm tones) → Amber accent
> - Pantone 2026 "Cloud Dancer" (soft white) → Light mode consideration
> - "Transformative Teal" trend → Primary brand color
> - Dark mode preference (70% of developers) → Dark-first design
> - Differentiation from purple-heavy AI market → Teal-forward approach

#### Primary Brand Colors

| Color | Hex | Tailwind | Usage | Psychology |
|-------|-----|----------|-------|------------|
| **Teal** | `#0D9488` | teal-600 | Primary CTA, brand identity | Innovation, trust, freshness |
| **Teal Light** | `#14B8A6` | teal-500 | Gradients, hover states | Energy, growth, cloud association |
| **Sky Blue** | `#0EA5E9` | sky-500 | Links, secondary actions | Technology, reliability, clarity |

> **Why Teal?** Differentiates from purple-heavy AI competitors (Claude, Jasper, etc.). Connects semantically to "Cloud" (sky, water, ethereal). Trending as "Transformative Teal" for 2025-2026.

#### Accent Colors

| Color | Hex | Tailwind | Usage | Psychology |
|-------|-----|----------|-------|------------|
| **Amber** | `#F59E0B` | amber-500 | Highlights, warmth, attention | Warmth (2025 trend), energy |
| **Violet** | `#8B5CF6` | violet-500 | **AI features only** | AI/future, premium (used sparingly) |

> **Violet Strategy**: Reserved exclusively for AI-specific features. This makes it more impactful when used and differentiates from competitors who overuse purple.

#### Semantic Colors

| Color | Hex | Tailwind | Usage |
|-------|-----|----------|-------|
| **Success** | `#10B981` | emerald-500 | Active, online, success states |
| **Warning** | `#F59E0B` | amber-500 | Warnings, pending states |
| **Error** | `#EF4444` | red-500 | Errors, destructive actions |
| **Info** | `#0EA5E9` | sky-500 | Information, tips |

#### Dark Mode Surfaces (Primary)

| Role | Hex | Tailwind | Notes |
|------|-----|----------|-------|
| **Background** | `#0F172A` | slate-900 | Rich dark with subtle blue undertone |
| **Surface 1** | `#1E293B` | slate-800 | Cards, panels, modals |
| **Surface 2** | `#334155` | slate-700 | Hover states, elevated elements |
| **Border** | `#475569` | slate-600 | Subtle borders, dividers |
| **Muted Text** | `#94A3B8` | slate-400 | Secondary text, placeholders |
| **Primary Text** | `#F8FAFC` | slate-50 | High contrast text |

> **Dark Mode First**: 70% of developers prefer dark mode. Dark backgrounds also complement VNC viewer screenshots and create a premium, focused feel.

#### Light Mode Surfaces (Secondary)

| Role | Hex | Tailwind | Notes |
|------|-----|----------|-------|
| **Background** | `#FFFFFF` | white | Clean, minimal |
| **Surface 1** | `#F8FAFC` | slate-50 | Cards, panels |
| **Surface 2** | `#F1F5F9` | slate-100 | Elevated elements |
| **Border** | `#E2E8F0` | slate-200 | Subtle separation |
| **Muted Text** | `#64748B` | slate-500 | Secondary text |
| **Primary Text** | `#0F172A` | slate-900 | High contrast |

#### Signature Gradient (2026 Edition)

```css
/* DeskCloud Signature Gradient - Teal to Sky to Violet */
.deskcloud-gradient {
  background: linear-gradient(135deg, #0D9488 0%, #0EA5E9 60%, #8B5CF6 100%);
}

/* Subtle ambient glow for hero sections */
.ambient-glow {
  background: radial-gradient(ellipse at top, rgba(13, 148, 136, 0.2) 0%, transparent 60%);
}

/* AI feature highlight gradient (use sparingly) */
.ai-gradient {
  background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
}

/* Premium metallic accent (2026 trend) */
.metallic-accent {
  background: linear-gradient(135deg, #E2E8F0 0%, #94A3B8 50%, #E2E8F0 100%);
}
```

#### Color Validation Summary

| Trend | How DeskCloud Addresses It |
|-------|---------------------------|
| Transformative Teal (2025-2026) | ✅ Teal as primary brand color |
| Pantone 2025 warm tones | ✅ Amber accent color |
| Dark mode preference (70%) | ✅ Dark-first design |
| Metallic/chrome accents | ✅ Subtle metallic gradients |
| Differentiate from AI purple | ✅ Purple reserved for AI features only |
| "Cloud" semantic | ✅ Sky blues, ethereal tones |

---

### Typography

#### Font Stack

```css
/* Primary: Clean, modern, developer-friendly */
--font-sans: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Monospace: For code, technical elements */
--font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;

/* Display: For hero headlines (optional) */
--font-display: 'Cal Sans', 'Inter', sans-serif;
```

#### Type Scale

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| **Hero H1** | 48-72px | 700 (Bold) | 1.1 |
| **H1** | 36-48px | 600 (Semibold) | 1.2 |
| **H2** | 30-36px | 600 | 1.25 |
| **H3** | 24px | 600 | 1.3 |
| **H4** | 20px | 500 (Medium) | 1.4 |
| **Body** | 16px | 400 (Regular) | 1.6 |
| **Small** | 14px | 400 | 1.5 |
| **Caption** | 12px | 500 | 1.4 |

---

### Logo Concepts

#### Primary Mark

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│     ╭──────╮                                        │
│    ╱        ╲     DeskCloud                         │
│   │  ◉    ◉  │    ──────────                       │
│   │    ▽    │    AI Desktops in the Cloud          │
│    ╲________╱                                       │
│      ╱    ╲                                         │
│     ╱______╲    (Abstract cloud + monitor shape)   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Logo Direction Options**:

1. **Abstract Cloud-Monitor Hybrid** 
   - Combines cloud shape with monitor/screen silhouette
   - Gradient fill (blue → cyan)
   - Modern, minimal

2. **Geometric Cloud Stack**
   - Layered rectangles forming cloud shape
   - Represents "stacked" virtual desktops
   - Works well as favicon

3. **Terminal/Cloud Icon**
   - Cloud with terminal cursor (`_`) inside
   - Developer-focused, technical feel
   - Immediately communicates "cloud computing"

4. **"DC" Lettermark**
   - Stylized D and C interlock
   - Gradient treatment
   - Professional, memorable

**Recommended**: Option 1 or 3 for technical credibility with approachability.

---

### Visual Style Guidelines

#### Card Design (Dark Mode - 2025-2026 Validated)

```css
.card {
  background: #1E293B;  /* slate-800 */
  border: 1px solid #334155;  /* slate-700 */
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
}

.card:hover {
  border-color: #0D9488;  /* Teal */
  box-shadow: 0 0 20px rgba(13, 148, 136, 0.15);  /* Teal glow */
}

/* AI Feature Card (special treatment) */
.card-ai {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(168, 85, 247, 0.05) 100%);
  border-color: rgba(139, 92, 246, 0.3);
}
```

#### Button Styles (2025-2026 Validated)

```css
/* Primary CTA - Teal-forward gradient */
.btn-primary {
  background: linear-gradient(135deg, #0D9488 0%, #0EA5E9 100%);
  color: white;
  font-weight: 500;
  padding: 12px 24px;
  border-radius: 8px;
  transition: all 0.2s;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.4);  /* Teal glow */
}

/* Secondary - Ghost */
.btn-secondary {
  background: transparent;
  border: 1px solid #475569;  /* slate-600 */
  color: #F8FAFC;
}

.btn-secondary:hover {
  background: #334155;  /* slate-700 */
  border-color: #0D9488;  /* Teal */
}

/* AI Feature Button - Violet (use sparingly) */
.btn-ai {
  background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
  color: white;
}

.btn-ai:hover {
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);  /* Violet glow */
}
```

#### Glassmorphism (for overlays, modals)

```css
.glass {
  background: rgba(24, 24, 27, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

---

### UI Component Styling

#### Feature Cards (Landing Page)

```
┌─────────────────────────────────────┐
│  ┌───┐                              │
│  │ ⚡ │  Fast Startup               │
│  └───┘                              │
│                                     │
│  Sessions start in 1-3 seconds,    │
│  not minutes. Lightweight ~100MB    │
│  per session.                       │
│                                     │
└─────────────────────────────────────┘

- Icon: Gradient background or glow effect
- Title: Semibold, white
- Description: Muted gray (#71717A)
- Hover: Subtle border glow
```

#### Pricing Cards

```
┌─────────────────────────────────────┐
│           PRO (Recommended)         │  ← Badge with gradient
│              $29/mo                 │  ← Large, bold
│                                     │
│  ✓ 1,000 sessions/month            │
│  ✓ Priority support                 │
│  ✓ 5 concurrent sessions           │
│  ✓ Session analytics               │
│                                     │
│  ┌─────────────────────────────┐   │
│  │      Start Pro Trial        │   │  ← Gradient button
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘

- Recommended tier: Gradient border glow
- Other tiers: Subtle border
- Free tier: Slightly muted styling
```

#### Session Status Badges (2025-2026 Validated)

```css
.badge-active {
  background: rgba(16, 185, 129, 0.15);  /* emerald */
  color: #10B981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-processing {
  background: rgba(13, 148, 136, 0.15);  /* teal - brand color */
  color: #14B8A6;
  border: 1px solid rgba(13, 148, 136, 0.3);
  animation: pulse 2s infinite;
}

.badge-ai-running {
  background: rgba(139, 92, 246, 0.15);  /* violet - AI indicator */
  color: #A855F7;
  border: 1px solid rgba(139, 92, 246, 0.3);
  animation: pulse 2s infinite;
}

.badge-error {
  background: rgba(239, 68, 68, 0.15);  /* red */
  color: #EF4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.badge-idle {
  background: rgba(148, 163, 184, 0.15);  /* slate */
  color: #94A3B8;
  border: 1px solid rgba(148, 163, 184, 0.3);
}
```

---

### Imagery & Illustrations

#### Screenshot Style
- **VNC viewers**: Framed with subtle shadows, rounded corners
- **Desktop previews**: Show real browser content (Google, forms, etc.)
- **Dark theme consistency**: All screenshots in dark mode

#### Illustration Style
- **Line art with gradient accents**
- **Minimal, geometric shapes**
- **Blue/cyan/purple color scheme**
- **Subtle glow effects on key elements**

#### Icons
- **Library**: Lucide React (consistent, open-source)
- **Style**: Outlined (not filled), 1.5px stroke
- **Size**: 20px for UI, 24px for features, 48px for hero

---

### Motion & Animation

#### Micro-interactions
```css
/* Smooth transitions on all interactive elements */
* {
  transition: color 0.15s, background-color 0.15s, border-color 0.15s, 
              transform 0.2s, box-shadow 0.2s;
}

/* Subtle hover lift */
.interactive:hover {
  transform: translateY(-2px);
}

/* Loading pulse */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

#### Page Transitions
- **Fade in up**: Content enters from below
- **Stagger children**: List items animate sequentially
- **Duration**: 200-400ms
- **Easing**: `ease-out` or `cubic-bezier(0.4, 0, 0.2, 1)`

---

### Brand Voice & Copy Guidelines

#### Tone
- **Confident but not arrogant**: "We've built..." not "We're the best..."
- **Technical but accessible**: Explain, don't jargon-bomb
- **Empowering**: Focus on what users can achieve
- **Slightly playful**: Can use developer humor sparingly

#### Headlines
```
✅ "AI Agents that Control Virtual Desktops"
✅ "Let Claude browse the web for you"
✅ "Your API key. Your control."

❌ "Revolutionary AI-powered cloud computing paradigm"
❌ "The ultimate enterprise solution for..."
```

#### CTAs
```
Primary: "Get Started Free" / "Start Building"
Secondary: "View Documentation" / "See How It Works"
Upgrade: "Upgrade to Pro" / "Unlock More Sessions"
```

---

### Dark Mode First

DeskCloud is **dark mode first** because:

1. **Developer preference**: 70%+ of developers prefer dark mode
2. **Matches VNC viewers**: Dark borders blend with desktop previews
3. **Premium feel**: Darker interfaces feel more sophisticated
4. **Eye comfort**: Extended use for watching AI agents work

Light mode is supported but secondary.

---

### Tailwind CSS Configuration (2025-2026 Validated)

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class', // Enable dark mode with class strategy
  theme: {
    extend: {
      colors: {
        // Brand colors (Teal-Forward for 2025-2026)
        brand: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',  // Light variant
          600: '#0d9488',  // PRIMARY - Main brand color
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
        // Sky for secondary actions
        sky: {
          400: '#38bdf8',
          500: '#0ea5e9',  // Secondary - Links
          600: '#0284c7',
        },
        // Accent colors
        accent: {
          amber: '#f59e0b',   // Warm accent (2025 trend)
          violet: '#8b5cf6',  // AI features ONLY
        },
        // Dark mode surfaces (slate-based)
        surface: {
          bg: '#0f172a',      // slate-900 - Background
          card: '#1e293b',    // slate-800 - Cards
          elevated: '#334155', // slate-700 - Hover/elevated
          border: '#475569',  // slate-600 - Borders
        },
        // Light mode surfaces
        'surface-light': {
          bg: '#ffffff',
          card: '#f8fafc',    // slate-50
          elevated: '#f1f5f9', // slate-100
          border: '#e2e8f0',  // slate-200
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        // DeskCloud signature gradients
        'gradient-brand': 'linear-gradient(135deg, #0d9488 0%, #0ea5e9 60%, #8b5cf6 100%)',
        'gradient-ambient': 'radial-gradient(ellipse at top, rgba(13, 148, 136, 0.2) 0%, transparent 60%)',
        'gradient-ai': 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
        'gradient-metallic': 'linear-gradient(135deg, #e2e8f0 0%, #94a3b8 50%, #e2e8f0 100%)',
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite alternate',
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(13, 148, 136, 0.3)' },  // Teal glow
          '100%': { boxShadow: '0 0 30px rgba(13, 148, 136, 0.6)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      boxShadow: {
        'glow-teal': '0 0 20px rgba(13, 148, 136, 0.4)',
        'glow-sky': '0 0 20px rgba(14, 165, 233, 0.4)',
        'glow-violet': '0 0 20px rgba(139, 92, 246, 0.4)',
      },
    },
  },
}
```

---

### Design Inspiration References (2025-2026)

| Product | What to Learn | Color Notes |
|---------|---------------|-------------|
| **Vercel** | Clean dark mode, typography, simplicity | Neutral, professional |
| **Linear** | Premium feel, smooth animations, card design | Purple accents (avoid copying) |
| **Raycast** | Developer-focused aesthetic, keyboard-first | Warm accents on dark |
| **Supabase** | Gradient accents, feature presentation | Green/teal tones ✓ |
| **Notion** | Clean UI, light/dark balance | Neutral with warmth |
| **Stripe** | Trust-building design, professional polish | Purple (differentiate from) |
| **Tailwind** | Developer appeal, teal brand | Teal/cyan ✓ |
| **Planetscale** | Tech credibility, dark mode | Purple (differentiate from) |

> **Differentiation Strategy**: Many AI/developer tools use purple (Claude, Linear, Stripe, Planetscale). DeskCloud's teal-forward approach stands out while still feeling premium and technical.

---

### Quick Reference: Color Tokens (2025-2026 Validated)

```css
:root {
  /* Backgrounds (Dark Mode - Primary) */
  --bg-primary: #0f172a;      /* slate-900 */
  --bg-secondary: #1e293b;    /* slate-800 */
  --bg-tertiary: #334155;     /* slate-700 */
  
  /* Text */
  --text-primary: #f8fafc;    /* slate-50 */
  --text-secondary: #cbd5e1;  /* slate-300 */
  --text-muted: #94a3b8;      /* slate-400 */
  
  /* Brand (Teal-Forward for 2026) */
  --brand-primary: #0d9488;   /* teal-600 - Main brand */
  --brand-light: #14b8a6;     /* teal-500 - Gradients */
  --brand-secondary: #0ea5e9; /* sky-500 - Links */
  --brand-accent: #f59e0b;    /* amber-500 - Warmth */
  --brand-ai: #8b5cf6;        /* violet-500 - AI features only */
  
  /* Semantic */
  --success: #10b981;         /* emerald-500 */
  --warning: #f59e0b;         /* amber-500 */
  --error: #ef4444;           /* red-500 */
  --info: #0ea5e9;            /* sky-500 */
  
  /* Borders */
  --border-subtle: #334155;   /* slate-700 */
  --border-default: #475569;  /* slate-600 */
  --border-focus: #0d9488;    /* teal-600 */
  
  /* Gradients */
  --gradient-brand: linear-gradient(135deg, #0d9488 0%, #0ea5e9 60%, #8b5cf6 100%);
  --gradient-ambient: radial-gradient(ellipse at top, rgba(13, 148, 136, 0.2) 0%, transparent 60%);
}
```

---

## Related Plans

- **[Session Video Recording](./session_video_recording.md)** - Video recording feature that integrates with the dashboard:
  - `RecordingPlayer` component for viewing recordings
  - Session cards with recording status badges
  - Recording settings page
  - Recordings browser page
  - See [Section 11: Dashboard & Frontend Integration](./session_video_recording.md#11-dashboard--frontend-integration)

---

## Related Plans

- [Session Video Recording](./session_video_recording.md) - Premium feature (Pro tier)
- [Custom Image Builder](./custom_image_builder.md) - Premium feature (Team/Enterprise tier)
- [Multi-OS Support](./multi_os_support.md) - Android, Windows, Raspberry Pi support
- [Remote Agent Client](./remote_agent_client.md) - Control user's own Windows/macOS/Linux computers

---

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com)
- [Vercel Deployment](https://vercel.com/docs)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://auth0.com/blog/jwt-authentication-best-practices/)
