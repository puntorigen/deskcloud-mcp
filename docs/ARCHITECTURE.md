# Architecture Overview

**Author:** Pablo Schaffner

This document describes the architecture of the Claude Computer Use Backend system.

## Table of Contents

- [System Overview](#system-overview)
- [Layer Architecture](#layer-architecture)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Key Design Decisions](#key-design-decisions)

---

## System Overview

The Claude Computer Use Backend is a FastAPI-based application that provides:

1. **Session Management** - Create, manage, and persist chat sessions
2. **Agent Orchestration** - Run Claude's computer use agent with tool execution
3. **Real-time Streaming** - Server-Sent Events for live progress updates
4. **Virtual Desktop** - VNC access to watch agent actions

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Docker Container                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌────────────────────────────────────────────────┐ │
│  │   noVNC     │◄───┤              Virtual Desktop (X11)             │ │
│  │   :6080     │    │  Xvfb + Mutter + Firefox + Desktop Apps        │ │
│  └─────────────┘    └────────────────────────────────────────────────┘ │
│        ▲                              ▲                                 │
│        │                              │ Tool Execution                  │
│        │                              │                                 │
│  ┌─────┴─────────────────────────────┴─────────────────────────────┐  │
│  │                     FastAPI Backend (:8000)                      │  │
│  │                                                                   │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │  │
│  │  │  REST API   │  │ SSE Stream  │  │   Session Manager       │  │  │
│  │  │  /sessions  │  │  /stream    │  │   Agent Orchestration   │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │  │
│  │                              │                                   │  │
│  │  ┌───────────────────────────┴────────────────────────────┐     │  │
│  │  │              Anthropic Computer Use Agent              │     │  │
│  │  │  sampling_loop + ToolCollection (bash, computer, edit) │     │  │
│  │  └────────────────────────────────────────────────────────┘     │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              │                                         │
└──────────────────────────────┼─────────────────────────────────────────┘
                               │
                        ┌──────▼──────┐
                        │   SQLite    │
                        │  Database   │
                        └─────────────┘
```

---

## Layer Architecture

The application follows a clean three-layer architecture:

### 1. API Layer (`app/api/`)

**Purpose:** HTTP interface, request validation, response serialization

```
app/api/
├── routes/
│   ├── sessions.py      # Session CRUD + SSE streaming
│   └── health.py        # Health check endpoints
├── schemas/
│   ├── session.py       # Session request/response models
│   └── message.py       # Message models
└── deps.py              # FastAPI dependencies
```

**Responsibilities:**
- Route definitions with OpenAPI documentation
- Request validation via Pydantic schemas
- Response serialization
- Dependency injection (database sessions, repositories)
- Error handling with appropriate HTTP status codes

### 2. Service Layer (`app/services/`)

**Purpose:** Business logic, orchestration, external integrations

```
app/services/
├── session_manager.py   # Session lifecycle management
└── agent_runner.py      # Anthropic loop integration
```

**Responsibilities:**
- Session state management
- Agent execution coordination
- Event queue management for SSE
- Message persistence coordination

### 3. Data Layer (`app/db/`)

**Purpose:** Database models, persistence, queries

```
app/db/
├── models.py            # SQLAlchemy ORM models
├── session.py           # Database session factory
└── repositories/
    └── session_repo.py  # Data access operations
```

**Responsibilities:**
- ORM model definitions
- Async database session management
- CRUD operations via repository pattern
- Transaction handling

---

## Component Details

### SessionManager

The `SessionManager` class is the central orchestrator:

```python
class SessionManager:
    """
    Manages chat sessions and agent execution.
    
    Key methods:
    - create_session(): Create new chat session
    - send_message(): Send user message and start agent
    - iter_events(): Async generator for SSE events
    - cancel_processing(): Stop running agent
    """
```

**State Management:**
- Tracks active sessions in memory
- Associates each session with its AgentRunner
- Manages event queues for SSE streaming

### AgentRunner

The `AgentRunner` wraps Anthropic's `sampling_loop`:

```python
class AgentRunner:
    """
    Wraps sampling_loop with event streaming callbacks.
    
    Flow:
    1. Receives user message
    2. Creates async event queue
    3. Runs sampling_loop with custom callbacks
    4. Callbacks push events to queue
    5. SSE endpoint consumes queue
    """
```

**Callback Integration:**
- `output_callback`: Receives text/tool_use blocks → emits events
- `tool_output_callback`: Receives tool results → emits events
- `api_response_callback`: Logs API responses

### Event System

Events are defined in `app/core/events.py`:

```python
class EventType(StrEnum):
    MESSAGE_START = "message_start"
    TEXT = "text"
    THINKING = "thinking"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    MESSAGE_COMPLETE = "message_complete"
    ERROR = "error"
    KEEPALIVE = "keepalive"
```

Events are serialized to SSE format:
```
event: text
data: {"content": "I'll help you...", "timestamp": "..."}

```

---

## Data Flow

### Message Send Flow

```
┌────────┐     ┌─────────┐     ┌───────────────┐     ┌────────────┐
│Frontend│     │ FastAPI │     │SessionManager │     │AgentRunner │
└───┬────┘     └────┬────┘     └──────┬────────┘     └─────┬──────┘
    │               │                 │                    │
    │ POST /messages│                 │                    │
    │──────────────>│                 │                    │
    │               │ send_message()  │                    │
    │               │────────────────>│                    │
    │               │                 │ create runner      │
    │               │                 │───────────────────>│
    │               │                 │                    │
    │               │                 │ run(message)       │
    │               │                 │───────────────────>│
    │               │                 │                    │
    │  {stream_url} │                 │                    │
    │<──────────────│                 │                    │
    │               │                 │                    │
    │ GET /stream   │                 │                    │
    │═══════════════│                 │                    │
    │               │                 │      [events]      │
    │<══════════════│<════════════════│<═══════════════════│
    │               │                 │                    │
```

### Event Flow (SSE)

```
AgentRunner                     SessionManager                  Client
     │                               │                            │
     │ sampling_loop starts          │                            │
     │───────────────────────────────│                            │
     │                               │                            │
     │ output_callback(text)         │                            │
     │──────────────────────>│       │                            │
     │                       ▼       │                            │
     │               queue.put(event)│                            │
     │                               │                            │
     │                               │  event: text               │
     │                               │  data: {...}               │
     │                               │═══════════════════════════>│
     │                               │                            │
     │ tool_output_callback(result)  │                            │
     │──────────────────────>│       │                            │
     │                       ▼       │                            │
     │               queue.put(event)│                            │
     │                               │  event: tool_result        │
     │                               │  data: {...}               │
     │                               │═══════════════════════════>│
     │                               │                            │
     │ loop completes                │                            │
     │──────────────────────>│       │                            │
     │                       ▼       │                            │
     │           queue.put(complete) │                            │
     │                               │  event: message_complete   │
     │                               │  data: {...}               │
     │                               │═══════════════════════════>│
```

---

## Key Design Decisions

### 1. SSE over WebSocket

**Decision:** Use Server-Sent Events for real-time streaming

**Rationale:**
- One-way server→client is sufficient (client uses REST for input)
- Built-in browser reconnection via EventSource API
- Works through HTTP proxies without upgrade
- Simpler implementation and debugging

### 2. Async Queue for Event Bridging

**Decision:** Use `asyncio.Queue` to connect sync callbacks to async SSE

**Rationale:**
- Anthropic's callbacks are synchronous
- SSE endpoint is async
- Queue provides thread-safe bridging
- Allows backpressure handling

### 3. Repository Pattern

**Decision:** Abstract database operations behind repositories

**Rationale:**
- Cleaner service layer code
- Easier to test (can mock repositories)
- Single responsibility - repositories only do data access
- Easy to swap database implementations

### 4. Single Container Deployment

**Decision:** Run all services in one Docker container

**Rationale:**
- Matches original Anthropic demo pattern
- Simplifies deployment for demo purposes
- VNC requires X11 stack in same environment as tools
- Can be split for production if needed

### 5. SQLite Default with PostgreSQL Ready

**Decision:** Use SQLite for development, support PostgreSQL for production

**Rationale:**
- SQLite requires no setup for local development
- SQLAlchemy abstracts the difference
- Easy transition to PostgreSQL via connection string
- Async support via aiosqlite/asyncpg

---

## Future Considerations

### Scaling

For production deployment with multiple users:

1. **Multiple Containers** - One VNC container per active session
2. **Container Orchestration** - Kubernetes/ECS for scaling
3. **Redis** - For session state and pub/sub
4. **PostgreSQL** - For persistent storage
5. **Load Balancer** - With sticky sessions for SSE

### Security Enhancements

1. **Authentication** - JWT or session-based auth
2. **API Key Rotation** - Per-user API keys
3. **Audit Logging** - Track all agent actions
4. **Network Isolation** - Restrict agent's network access

