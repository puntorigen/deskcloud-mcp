# Claude Computer Use Backend

**Author:** Pablo Schaffner

A production-ready FastAPI backend for managing Claude Computer Use agent sessions with real-time streaming, persistent storage, and VNC integration.

## 🎯 Overview

This project transforms the Anthropic Computer Use demo from an experimental Streamlit interface into a scalable backend API with:

- **RESTful API** for session and message management
- **Server-Sent Events (SSE)** for real-time agent updates
- **SQLite/PostgreSQL** persistence for chat history
- **VNC Integration** for watching agent actions
- **Modern Frontend** with clean three-panel design

## 🏗️ Architecture

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
│  │  REST API          │  SSE Streaming    │  Session Manager        │  │
│  │  /api/v1/sessions  │  Real-time events │  Agent orchestration    │  │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                         │
└──────────────────────────────┼─────────────────────────────────────────┘
                               │
                        ┌──────▼──────┐
                        │   SQLite    │
                        │  (Sessions) │
                        └─────────────┘
```

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
| **VNC Viewer** | http://localhost:6080/vnc.html | Virtual desktop |
| **API** | http://localhost:8000/api/v1 | REST endpoints |

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
    "content": "Search the weather in Dubai"
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

### Use Case 1: Weather Search (Dubai)

1. **Create a new session** via the "New Session" button
2. **Enter the prompt**: "Search the weather in Dubai"
3. **Watch** the agent:
   - Open Firefox
   - Navigate to Google
   - Search for weather
   - Provide summarized results
4. **View real-time progress** in the chat panel

### Use Case 2: Weather Search (San Francisco)

1. **Create another session**
2. **Enter the prompt**: "Search the weather in San Francisco"
3. **Verify** both sessions maintain separate histories

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
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration settings
│   ├── api/
│   │   ├── routes/
│   │   │   ├── sessions.py     # Session CRUD & streaming
│   │   │   └── health.py       # Health endpoints
│   │   ├── schemas/            # Pydantic models
│   │   └── deps.py             # Dependencies
│   ├── services/
│   │   ├── session_manager.py  # Session orchestration
│   │   └── agent_runner.py     # Anthropic loop wrapper
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
├── docker-compose.yml
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

## 🔒 Security Considerations

1. **API Key Protection**: Never expose `ANTHROPIC_API_KEY` to the frontend
2. **Input Sanitization**: All user input is sanitized via Pydantic + bleach
3. **Rate Limiting**: Configurable limits on API endpoints
4. **CORS**: Restricted origins in production

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
| `ANTHROPIC_API_KEY` | Claude API key (required) | - |
| `API_PROVIDER` | anthropic, bedrock, vertex | anthropic |
| `DATABASE_URL` | Database connection string | sqlite |
| `DEBUG` | Enable debug mode | false |
| `CORS_ORIGINS` | Allowed CORS origins | localhost |

## 📚 Documentation

Detailed documentation for developers is available in the `docs/` folder:

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, layer architecture, data flow |
| [API.md](docs/API.md) | Complete API reference with examples |
| [DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local setup, code style, testing guide |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Docker, Render.com, production deployment |

## 📝 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com) for the Computer Use demo and Claude API
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [noVNC](https://novnc.com/) for browser-based VNC

