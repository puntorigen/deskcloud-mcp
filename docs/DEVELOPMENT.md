# Development Guide

**Author:** Pablo Schaffner

This guide covers setting up a development environment and contributing to the codebase.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)

---

## Prerequisites

### Required

- **Python 3.11+** - The application uses modern Python features
- **Docker & Docker Compose** - For running the full stack
- **Git** - Version control

### Recommended

- **VS Code or Cursor** - With Python extension
- **HTTPie or curl** - For API testing
- **A VNC client** - For direct VNC connections (optional)

---

## Local Setup

### Option 1: Docker Development (Recommended)

The easiest way to run the full stack:

```bash
# Clone the repository
cd deskcloud-mcp

# Copy environment template
cp .env.example .env

# Edit .env and add your Anthropic API key
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# Build and run
docker-compose up --build

# Access:
# - Frontend: http://localhost:8080
# - API Docs: http://localhost:8000/docs
# - VNC: http://localhost:6080/vnc.html
```

### Option 2: Local Python Development

For faster iteration on backend code (without VNC/agent functionality):

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY=sk-ant-your-key  # Optional for API-only testing
export DATABASE_URL=sqlite+aiosqlite:///./data/sessions.db

# Run the API server with auto-reload
uvicorn app.main:app --reload --port 8000

# In another terminal, serve frontend
python -m http.server 8080 --directory frontend
```

### Option 3: Hybrid Development

Mount local code into Docker for live reloading:

```bash
# Uncomment these lines in docker-compose.yml:
# volumes:
#   - ./app:/home/computeruse/app
#   - ./frontend:/home/computeruse/frontend

docker-compose up --build
```

---

## Project Structure

```
deskcloud-mcp/
├── app/                          # Backend Python package
│   ├── __init__.py               # Package init, version
│   ├── main.py                   # FastAPI app, middleware, lifecycle
│   ├── config.py                 # Pydantic settings
│   │
│   ├── api/                      # API layer
│   │   ├── routes/               # Route handlers
│   │   │   ├── sessions.py       # Session CRUD + streaming
│   │   │   └── health.py         # Health endpoints
│   │   ├── schemas/              # Pydantic models
│   │   │   ├── session.py        # Session schemas
│   │   │   └── message.py        # Message schemas
│   │   └── deps.py               # Dependencies (DI)
│   │
│   ├── services/                 # Business logic
│   │   ├── session_manager.py    # Session orchestration
│   │   └── agent_runner.py       # Anthropic integration
│   │
│   ├── db/                       # Data layer
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── session.py            # DB session factory
│   │   └── repositories/         # Data access
│   │       └── session_repo.py   # Session repository
│   │
│   └── core/                     # Shared utilities
│       └── events.py             # SSE event types
│
├── frontend/                     # Static frontend
│   ├── index.html                # Main HTML
│   ├── css/
│   │   └── styles.css            # Stylesheet
│   └── js/
│       ├── api.js                # API client
│       ├── sse.js                # SSE handler
│       └── app.js                # Main app logic
│
├── docker/                       # Docker configuration
│   ├── Dockerfile                # Image definition
│   └── entrypoint.sh             # Startup script
│
├── tests/                        # Test suite
│   ├── conftest.py               # Pytest fixtures
│   ├── test_sessions.py          # Session tests
│   └── test_streaming.py         # SSE tests
│
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md           # System design
│   ├── API.md                    # API reference
│   ├── DEVELOPMENT.md            # This file
│   └── DEPLOYMENT.md             # Deployment guide
│
├── docker-compose.yml            # Docker Compose config
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Project metadata
├── .env.example                  # Environment template
└── README.md                     # Project overview
```

---

## Development Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes** to the code

3. **Run tests**
   ```bash
   pytest tests/ -v
   ```

4. **Test manually** via the frontend or API docs

5. **Commit with descriptive message**
   ```bash
   git commit -m "feat: add new endpoint for X"
   ```

### Adding a New Endpoint

1. **Define schema** in `app/api/schemas/`
   ```python
   # schemas/my_feature.py
   class MyRequest(BaseModel):
       field: str
   ```

2. **Add repository method** if needed in `app/db/repositories/`

3. **Add service method** if needed in `app/services/`

4. **Create route** in `app/api/routes/`
   ```python
   @router.post("/my-endpoint")
   async def my_endpoint(body: MyRequest):
       pass
   ```

5. **Register route** in `app/api/routes/__init__.py`

6. **Write tests** in `tests/`

### Adding a New SSE Event Type

1. **Add to EventType enum** in `app/core/events.py`
   ```python
   class EventType(StrEnum):
       MY_EVENT = "my_event"
   ```

2. **Create helper function**
   ```python
   def my_event(data: str, message_id: str | None = None) -> Event:
       return create_event(EventType.MY_EVENT, message_id, data=data)
   ```

3. **Emit from AgentRunner** or SessionManager

4. **Handle in frontend** `js/sse.js`

---

## Code Style

### Python

- **Formatter:** Black (line length 100)
- **Linter:** Ruff
- **Type hints:** Required for all functions
- **Docstrings:** Google style for public functions

```python
def process_message(
    session_id: str,
    content: str,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """
    Process a user message.
    
    Args:
        session_id: Target session identifier
        content: Message content to process
        timeout: Maximum processing time in seconds
    
    Returns:
        Dict containing message_id and status
    
    Raises:
        ValueError: If session is not active
    """
    pass
```

### JavaScript

- **Style:** Modern ES6+
- **Classes:** Used for major components (ApiClient, SSEClient, ComputerUseApp)
- **Comments:** JSDoc for public methods

```javascript
/**
 * Send a message to a session.
 * @param {string} sessionId - Session ID
 * @param {string} content - Message content
 * @returns {Promise<Object>} Response with stream URL
 */
async sendMessage(sessionId, content) {
    // ...
}
```

### CSS

- **Methodology:** BEM-like naming
- **Variables:** CSS custom properties for theming
- **Organization:** Grouped by component

```css
.session-item { }
.session-item__title { }
.session-item__meta { }
.session-item--active { }
```

---

## Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific file
pytest tests/test_sessions.py -v

# Specific test
pytest tests/test_sessions.py::TestSessionCRUD::test_create_session -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Writing Tests

```python
# tests/test_my_feature.py
import pytest
from httpx import AsyncClient

class TestMyFeature:
    @pytest.mark.asyncio
    async def test_something(self, client: AsyncClient):
        response = await client.post("/api/v1/my-endpoint", json={})
        assert response.status_code == 200
```

### Test Fixtures

Available fixtures in `conftest.py`:

- `client` - Async HTTP client for API requests
- `db_session` - Clean database session
- `test_session` - Pre-created session for testing

---

## Debugging

### API Debugging

1. **Use FastAPI's interactive docs**
   - http://localhost:8000/docs (Swagger)
   - http://localhost:8000/redoc (ReDoc)

2. **Enable debug mode**
   ```bash
   export DEBUG=true
   ```

3. **Check logs**
   ```bash
   docker-compose logs -f app
   ```

### SSE Debugging

Browser DevTools → Network tab → Filter by "EventStream"

### Database Debugging

```python
# Enable SQL logging
export DATABASE_ECHO=true
```

Or inspect SQLite directly:
```bash
sqlite3 data/sessions.db
.tables
SELECT * FROM sessions;
```

### VNC Debugging

- Direct VNC: `vnc://localhost:5900`
- Web VNC: http://localhost:6080/vnc.html
- Check X11 logs: `/tmp/xvfb.log`

---

## Common Tasks

### Reset Database

```bash
rm -f data/sessions.db
# Restart application - tables will be recreated
```

### Update Dependencies

```bash
pip install -U -r requirements.txt
# Update requirements.txt with new versions
pip freeze > requirements.txt
```

### Build Docker Image

```bash
docker build -f docker/Dockerfile -t deskcloud-mcp:local .
```

### Run Single Service

```bash
# Just the API (no VNC)
uvicorn app.main:app --reload

# Just frontend
python -m http.server 8080 --directory frontend
```

### Check API Health

```bash
curl http://localhost:8000/api/v1/health | jq
```

### Create Test Session via CLI

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Session"}' | jq
```

---

## Troubleshooting

### "Module not found" errors

```bash
# Ensure PYTHONPATH includes the project root
export PYTHONPATH=/path/to/deskcloud-mcp
```

### Database locked errors

SQLite doesn't support concurrent writes well. Ensure only one process accesses the database, or switch to PostgreSQL for concurrent access.

### VNC not connecting

Check that X11 services are running:
```bash
docker-compose exec app ps aux | grep -E "Xvfb|x11vnc|mutter"
```

### SSE connection dropping

- Check proxy timeout settings
- Ensure `X-Accel-Buffering: no` header is set
- Browser may limit concurrent EventSource connections (max 6 per domain)

