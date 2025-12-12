# Claude Computer Use Backend

A production-ready FastAPI backend for managing Claude Computer Use agent sessions with real-time streaming, persistent storage, VNC integration, and **MCP (Model Context Protocol) support**.

## 🎯 Overview

This project transforms the Anthropic Computer Use demo from an experimental Streamlit interface into a scalable backend API with:

- **Multi-Session Concurrency** - Each session gets an isolated virtual desktop
- **Filesystem Isolation** - Each session has isolated HOME, downloads, and browser profiles (OverlayFS)
- **MCP Server** - Connect from Cursor IDE or Claude Desktop via Model Context Protocol
- **RESTful API** for session and message management
- **Server-Sent Events (SSE)** for real-time agent updates
- **SQLite/PostgreSQL** persistence for chat history
- **VNC Integration** for watching agent actions per session
- **Auto-Cleanup** - Sessions auto-destroy after 1 hour of inactivity
- **Modern Frontend** with clean three-panel design

## 🏗️ Architecture

### Multi-Session Support

Each session gets its own **isolated X11 display**, enabling true concurrent usage:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Docker Container                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI + MCP Server (:8000)                     │ │
│  │                                                                      │ │
│  │  /api/v1/*   REST API          │  /mcp   MCP Protocol (Cursor)     │ │
│  │  /llms.txt   LLM Documentation │  /docs  Swagger UI                │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │                                           │
│                    ┌─────────┴─────────┐                                │
│                    │  Display Manager  │                                │
│                    │ Filesystem Manager│                                │
│                    │  Session Manager  │                                │
│                    └─────────┬─────────┘                                │
│                              │                                           │
│  ┌───────────────┬───────────┴───────────┬───────────────┐              │
│  │   Session 1   │      Session 2        │   Session 3   │   ...        │
│  │   Xvfb :1     │      Xvfb :2          │   Xvfb :3     │              │
│  │   VNC :5901   │      VNC :5902        │   VNC :5903   │              │
│  │   noVNC :6081 │      noVNC :6082      │   noVNC :6083 │              │
│  │  ┌─────────┐  │     ┌─────────┐       │  ┌─────────┐  │              │
│  │  │ Firefox │  │     │ Firefox │       │  │ Firefox │  │              │
│  │  │ (own fs)│  │     │ (own fs)│       │  │ (own fs)│  │              │
│  │  └─────────┘  │     └─────────┘       │  └─────────┘  │              │
│  └───────────────┴───────────────────────┴───────────────┘              │
│                                                                          │
│  Each session: ~100MB RAM, isolated display + filesystem                │
└─────────────────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

| Feature | Benefit |
|---------|---------|
| **Isolated Desktops** | Each session has its own X11 display |
| **Isolated Filesystems** | Each session has its own HOME, downloads, browser profile (OverlayFS) |
| **Persistent State** | Browser tabs, forms, files persist per session |
| **Fast Startup** | 1-3 seconds (vs 10-30s for container orchestration) |
| **Low Memory** | ~100MB per session (vs ~1GB for containers) |
| **Efficient Storage** | Copy-on-write means only changed files use disk |
| **Render.com Ready** | No Docker socket needed |

### Session Isolation

Each session is fully isolated:

```
Session 1:                          Session 2:
┌─────────────────────┐            ┌─────────────────────┐
│  Display: :1        │            │  Display: :2        │
│  VNC: 5901          │            │  VNC: 5902          │
├─────────────────────┤            ├─────────────────────┤
│  /home/user/        │            │  /home/user/        │
│    Downloads/       │ (isolated) │    Downloads/       │
│    .mozilla/        │            │    .mozilla/        │
│    .config/         │            │    .config/         │
└─────────────────────┘            └─────────────────────┘
         │                                  │
         └──────────┬───────────────────────┘
                    │
           ┌────────▼────────┐
           │   Base Layer    │
           │   (shared,      │
           │   read-only)    │
           │   ~500MB        │
           └─────────────────┘
```

**OverlayFS** provides copy-on-write semantics:
- Shared base layer (OS, Firefox, apps) - one copy for all sessions
- Per-session upper layer - only stores changed files
- Disk cost: ~0 until session downloads or modifies files

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Anthropic API key ([get one here](https://console.anthropic.com/))

### 1. Clone and Setup

```bash
# Copy environment template
cp env.example .env

# Edit .env and add your API key
# ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 2. Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:8080 | Web interface |
| **API Docs** | http://localhost:8000/docs | Swagger documentation |
| **MCP Server** | http://localhost:8000/mcp | Model Context Protocol endpoint |
| **LLMs.txt** | http://localhost:8000/llms.txt | AI-readable documentation |
| **API** | http://localhost:8000/api/v1 | REST endpoints |

> **Note**: VNC URLs are now per-session. Each session returns its own `vnc_url` in the response.

## 🔌 MCP Integration (Cursor / Claude Desktop)

This server implements the **Model Context Protocol (MCP)**, allowing AI assistants to control the virtual desktop directly.

### BYOK (Bring Your Own Key)

The orchestration is **FREE** - you only pay for your own Anthropic API usage. Provide your API key in the MCP config:

```json
{
  "mcpServers": {
    "computer-use": {
      "url": "http://localhost:8000/mcp",
      "transport": "streamable-http",
      "headers": {
        "X-Anthropic-API-Key": "sk-ant-your-key-here"
      }
    }
  }
}
```

**Note:** The API key flows through infrastructure (HTTP headers), never through tool parameters. The LLM never sees your API key.

### Configure Cursor IDE

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "computer-use": {
      "url": "http://localhost:8000/mcp",
      "transport": "streamable-http",
      "headers": {
        "X-Anthropic-API-Key": "sk-ant-your-key-here"
      }
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `create_session` | Create a new session with isolated desktop |
| `execute_task` | Execute a task (long-running, agent controls desktop) |
| `get_session_status` | Check session status and TTL remaining |
| `destroy_session` | Manually destroy a session |
| `take_screenshot` | Capture current desktop state |

### Example Cursor Workflow

```
User: "Create a session and search for flights to Tokyo on Google"

Cursor (via MCP):
1. create_session() → gets session_id, vnc_url
2. execute_task(session_id, "search for flights to Tokyo on Google")
3. Agent opens Firefox, navigates, searches, returns results
4. Session auto-destroys after 1 hour of inactivity
```

## 📖 API Reference

### Session Management

#### Create Session
```bash
POST /api/v1/sessions
Content-Type: application/json

{
    "title": "Weather Search Task",
    "model": "claude-sonnet-4-5-20250929"
}
```

#### List Sessions
```bash
GET /api/v1/sessions?limit=50&offset=0
```

#### Get Session with History
```bash
GET /api/v1/sessions/{session_id}
```

#### Delete Session
```bash
DELETE /api/v1/sessions/{session_id}
```

### Agent Interaction

#### Send Message
```bash
POST /api/v1/sessions/{session_id}/messages
Content-Type: application/json

{
    "content": "Search the weather in Santiago, Chile"
}
```

#### Stream Events (SSE)
```bash
GET /api/v1/sessions/{session_id}/stream
Accept: text/event-stream
```

**Event Types:**
- `text` - Agent text response
- `thinking` - Extended thinking content
- `tool_use` - Tool invocation (screenshot, click, etc.)
- `tool_result` - Tool execution result
- `message_complete` - Processing finished
- `error` - Error notification

#### Cancel Processing
```bash
POST /api/v1/sessions/{session_id}/cancel
```

### Health & Config

```bash
GET /api/v1/health         # Health check
GET /api/v1/health/ready   # Readiness probe
GET /api/v1/config         # Configuration info
```

## 🎬 Usage Demo

### Use Case 1: Weather Search (Santiago, Chile)

1. **Create a new session** via the "New Session" button
2. **Enter the prompt**: "Search the weather in Santiago, Chile"
3. **Watch** the agent:
   - Open Firefox
   - Navigate to Google
   - Search for weather
   - Provide summarized results
4. **View real-time progress** in the chat panel

### Use Case 2: Concurrent Sessions

1. **Create another session** (while Session 1 is still active)
2. **Enter the prompt**: "Search the weather in San Francisco"
3. **Both sessions run independently** with:
   - Separate VNC viewers (different ports)
   - Isolated browser state (tabs, cookies, history)
   - Independent chat histories

## 🔧 Development

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --reload --port 8000

# In another terminal, serve the frontend
python -m http.server 8080 --directory frontend
```

### Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application + MCP mounting
│   ├── config.py               # Configuration settings
│   ├── api/
│   │   ├── routes/
│   │   │   ├── sessions.py     # Session CRUD & streaming
│   │   │   ├── health.py       # Health endpoints
│   │   │   └── llms.py         # LLMs.txt endpoint
│   │   ├── schemas/            # Pydantic models
│   │   └── deps.py             # Dependencies
│   ├── mcp/                    # MCP Server
│   │   ├── __init__.py
│   │   ├── server.py           # FastMCP setup
│   │   └── tools.py            # MCP tool implementations
│   ├── services/
│   │   ├── session_manager.py     # Session orchestration
│   │   ├── display_manager.py     # Multi-display management
│   │   ├── filesystem_manager.py  # OverlayFS isolation
│   │   ├── session_cleanup.py     # Auto-cleanup service
│   │   └── agent_runner.py        # Anthropic loop wrapper
│   ├── db/
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── session.py          # DB session factory
│   │   └── repositories/       # Data access layer
│   └── core/
│       └── events.py           # SSE event types
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   └── js/
│       ├── api.js              # API client
│       ├── sse.js              # SSE handling
│       └── app.js              # Main application
├── docker/
│   ├── Dockerfile
│   └── entrypoint.sh
├── docs/
│   └── plans/                  # Architecture documentation
├── docker-compose.yml
├── render.yaml                 # Render.com deployment
├── requirements.txt
└── README.md
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v
```

## ⏱️ Session Lifecycle & TTL

Sessions automatically clean up to prevent resource exhaustion:

```
Create ──► Active ──► Idle (no activity) ──► Auto-Destroyed
              │
              └──► Processing ──► Active
```

- **Default TTL**: 1 hour of inactivity
- **Cleanup Check**: Every 5 minutes
- **Manual Cleanup**: Use `DELETE /api/v1/sessions/{id}` or MCP `destroy_session`
- **Resource Usage**: ~100MB RAM per session

## 🔒 Security Considerations

1. **API Key Protection**: Never expose `ANTHROPIC_API_KEY` to the frontend
2. **Display Isolation**: Each session has isolated X11 display (no cross-session access)
3. **Filesystem Isolation**: Each session has isolated HOME, downloads, browser profile (OverlayFS)
4. **No Session Enumeration**: `list_sessions` disabled in MCP for privacy (requires auth)
5. **Input Sanitization**: All user input is sanitized via Pydantic + bleach
6. **Rate Limiting**: Configurable limits on API endpoints
7. **CORS**: Restricted origins in production

## 📊 Sequence Diagram

```
┌────────┐          ┌─────────┐          ┌─────────────┐          ┌───────┐
│Frontend│          │ FastAPI │          │SessionManager│          │Claude │
└───┬────┘          └────┬────┘          └──────┬──────┘          └───┬───┘
    │  POST /sessions    │                      │                     │
    │───────────────────>│  create_session()    │                     │
    │<───────────────────│<─────────────────────│                     │
    │                    │                      │                     │
    │  POST /sessions/{id}/messages             │                     │
    │───────────────────>│  send_message()      │                     │
    │<───────────────────│                      │                     │
    │                    │                      │                     │
    │  GET /stream (SSE) │                      │                     │
    │═══════════════════>│                      │  sampling_loop()    │
    │                    │                      │────────────────────>│
    │                    │                      │                     │
    │  event: text       │◄─────────────────────│◄────────────────────│
    │<═══════════════════│                      │                     │
    │                    │                      │                     │
    │  event: tool_use   │◄─────────────────────│◄────────────────────│
    │<═══════════════════│                      │                     │
    │                    │                      │                     │
    │  event: tool_result│◄─────────────────────│                     │
    │<═══════════════════│                      │                     │
    │                    │                      │                     │
    │  event: complete   │◄─────────────────────│◄────────────────────│
    │<═══════════════════│                      │                     │
```

## 🌐 Deployment Options

### Local Docker

```bash
docker-compose up -d
```

### Render.com

For Render.com deployment, use the single-port architecture with nginx proxying. Configure a single web service exposing port 8080, which proxies to the FastAPI backend, noVNC server, and static files.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key (server default, see BYOK below) | - |
| `API_PROVIDER` | anthropic, bedrock, vertex | anthropic |
| `DATABASE_URL` | Database connection string | sqlite |
| `SESSION_TTL_SECONDS` | Session idle timeout | 3600 (1 hour) |
| `CLEANUP_INTERVAL_SECONDS` | Cleanup check interval | 300 (5 min) |
| `MCP_ENABLED` | Enable MCP server | true |
| `MAX_DISPLAYS` | Max concurrent sessions | 20 |
| `FILESYSTEM_ISOLATION_ENABLED` | Enable OverlayFS isolation | true |
| `SESSION_DISK_QUOTA_MB` | Per-session disk quota | 500 |
| `DEBUG` | Enable debug mode | false |
| `CORS_ORIGINS` | Allowed CORS origins | localhost |

## 📚 Documentation

Detailed documentation for developers is available in the `docs/` folder:

| Document | Description |
|----------|-------------|
| [API.md](docs/API.md) | Complete API reference with examples |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, layer architecture, data flow |
| [DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local setup, code style, testing guide |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Docker, Render.com, production deployment |
| [plans/multi_session_scaling.md](docs/plans/multi_session_scaling.md) | Multi-display architecture design |
| [plans/session_filesystem_isolation.md](docs/plans/session_filesystem_isolation.md) | OverlayFS filesystem isolation |
| [plans/session_snapshots.md](docs/plans/session_snapshots.md) | CRIU-based session snapshots (future) |
| [plans/session_video_recording.md](docs/plans/session_video_recording.md) | FFmpeg-based session recording (proposed) |
| [plans/mcp_server_transformation.md](docs/plans/mcp_server_transformation.md) | MCP server implementation plan |

## 📝 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com) for the Computer Use demo and Claude API
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [noVNC](https://novnc.com/) for browser-based VNC

