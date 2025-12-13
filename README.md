# DeskCloud MCP

Open source MCP (Model Context Protocol) server for AI-controlled virtual desktops.

DeskCloud MCP provides:

- **Multi-session virtual desktops** (isolated X11 display per session)
- **Real-time streaming** via Server-Sent Events (SSE)
- **MCP endpoint** for Cursor / Claude Desktop integrations
- **VNC/noVNC** so you can watch what the agent is doing
- **SQLite** persistence (PostgreSQL optional)

## Quick start (Docker)

### Prerequisites

- Docker + Docker Compose
- Anthropic API key (set it as an env var or provide it via MCP headers)

### Run

```bash
# Create local env file
cp .env.example .env

# Set your ANTHROPIC_API_KEY in .env

# Build and start
docker-compose up --build
```

### URLs

- Frontend: `http://localhost:8080`
- API docs: `http://localhost:8000/docs`
- MCP endpoint: `http://localhost:8000/mcp`
- noVNC: `http://localhost:6080/vnc.html`

## MCP integration

### Cursor

Add a server to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "deskcloud-mcp": {
      "url": "http://localhost:8000/mcp",
      "transport": "streamable-http",
      "headers": {
        "X-Anthropic-API-Key": "<YOUR_ANTHROPIC_API_KEY>"
      }
    }
  }
}
```

### Available MCP tools

- `create_session`
- `execute_task`
- `get_session_status`
- `destroy_session`
- `take_screenshot`

## Local development (without Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Backend
uvicorn app.main:app --reload --port 8000

# Frontend
python -m http.server 8080 --directory frontend
```

## Documentation

- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/DEVELOPMENT.md`
- `docs/DEPLOYMENT.md`

## Security

See `SECURITY.md`.

## Contributing

See `CONTRIBUTING.md`.

## License

MIT (see `LICENSE`).
