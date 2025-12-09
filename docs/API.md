# API Reference

**Author:** Pablo Schaffner

Complete API documentation for the Claude Computer Use Backend.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, no authentication is required. The backend uses the `ANTHROPIC_API_KEY` environment variable for Claude API access.

---

## Sessions

### Create Session

Create a new chat session for agent interaction.

```http
POST /sessions
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Human-readable session title (auto-generated if empty) |
| `model` | string | No | Claude model identifier (default: claude-sonnet-4-5-20250929) |
| `provider` | string | No | API provider: `anthropic`, `bedrock`, `vertex` (default: anthropic) |
| `system_prompt_suffix` | string | No | Custom instructions appended to system prompt |

**Example Request:**

```json
{
    "title": "Weather Search Task",
    "model": "claude-sonnet-4-5-20250929",
    "provider": "anthropic"
}
```

**Response:** `201 Created`

```json
{
    "id": "sess_abc123def456",
    "title": "Weather Search Task",
    "status": "active",
    "model": "claude-sonnet-4-5-20250929",
    "provider": "anthropic",
    "created_at": "2024-12-07T10:30:00Z",
    "updated_at": "2024-12-07T10:30:00Z",
    "vnc_url": "http://localhost:6080/vnc.html"
}
```

---

### List Sessions

Retrieve all sessions with optional filtering.

```http
GET /sessions
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_archived` | boolean | false | Include archived sessions |
| `limit` | integer | 50 | Maximum results (1-100) |
| `offset` | integer | 0 | Results to skip |

**Example Request:**

```http
GET /sessions?limit=10&offset=0
```

**Response:** `200 OK`

```json
{
    "sessions": [
        {
            "id": "sess_abc123",
            "title": "Weather Search Task",
            "status": "active",
            "model": "claude-sonnet-4-5-20250929",
            "provider": "anthropic",
            "created_at": "2024-12-07T10:30:00Z",
            "updated_at": "2024-12-07T10:35:00Z",
            "vnc_url": "http://localhost:6080/vnc.html"
        }
    ],
    "total": 1
}
```

---

### Get Session

Retrieve a session with its complete message history.

```http
GET /sessions/{session_id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session identifier |

**Response:** `200 OK`

```json
{
    "id": "sess_abc123",
    "title": "Weather Search Task",
    "status": "active",
    "model": "claude-sonnet-4-5-20250929",
    "provider": "anthropic",
    "created_at": "2024-12-07T10:30:00Z",
    "updated_at": "2024-12-07T10:35:00Z",
    "vnc_url": "http://localhost:6080/vnc.html",
    "system_prompt_suffix": null,
    "messages": [
        {
            "id": "msg_001",
            "role": "user",
            "content": "Search the weather in Santiago, Chile",
            "tool_use_id": null,
            "timestamp": "2024-12-07T10:31:00Z"
        },
        {
            "id": "msg_002",
            "role": "assistant",
            "content": [
                {"type": "text", "text": "I'll search for Santiago, Chile weather..."},
                {"type": "tool_use", "id": "toolu_123", "name": "computer", "input": {...}}
            ],
            "tool_use_id": null,
            "timestamp": "2024-12-07T10:31:05Z"
        }
    ]
}
```

**Error Responses:**

- `404 Not Found` - Session does not exist or is archived

---

### Delete Session

Archive a session (soft delete).

```http
DELETE /sessions/{session_id}
```

**Response:** `204 No Content`

**Error Responses:**

- `404 Not Found` - Session does not exist

---

## Messages

### Send Message

Send a user message to the agent and start processing.

```http
POST /sessions/{session_id}/messages
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | Message content (1-10000 chars) |

**Example Request:**

```json
{
    "content": "Search the weather in Santiago, Chile"
}
```

**Response:** `200 OK`

```json
{
    "message_id": "msg_xyz789",
    "status": "processing",
    "stream_url": "/api/v1/sessions/sess_abc123/stream"
}
```

**Error Responses:**

- `404 Not Found` - Session does not exist
- `409 Conflict` - Session is already processing
- `422 Unprocessable Entity` - Invalid message content
- `503 Service Unavailable` - API key not configured

---

### Stream Events (SSE)

Connect to receive real-time agent updates.

```http
GET /sessions/{session_id}/stream
Accept: text/event-stream
```

**Response:** `200 OK` with `Content-Type: text/event-stream`

**Event Types:**

#### `message_start`
Processing has started.
```
event: message_start
data: {"message_id": "msg_xyz789", "timestamp": "2024-12-07T10:31:00Z"}
```

#### `text`
Text content from the agent.
```
event: text
data: {"content": "I'll search for the weather in Santiago, Chile...", "timestamp": "..."}
```

#### `thinking`
Extended thinking content (when enabled).
```
event: thinking
data: {"content": "Let me analyze the best approach...", "timestamp": "..."}
```

#### `tool_use`
Agent is invoking a tool.
```
event: tool_use
data: {"tool": "computer", "input": {"action": "screenshot"}, "tool_use_id": "toolu_123", "timestamp": "..."}
```

#### `tool_result`
Tool execution completed.
```
event: tool_result
data: {"tool_use_id": "toolu_123", "output": "Screenshot captured", "screenshot": "base64...", "timestamp": "..."}
```

#### `message_complete`
Processing finished.
```
event: message_complete
data: {"message_id": "msg_xyz789", "status": "completed", "timestamp": "..."}
```

#### `error`
An error occurred.
```
event: error
data: {"error": "Rate limit exceeded", "code": "RATE_LIMITED", "retry_after": 30}
```

#### `keepalive`
Connection maintenance (every 30s).
```
event: keepalive
data: {}
```

**JavaScript Example:**

```javascript
const eventSource = new EventSource('/api/v1/sessions/sess_abc123/stream');

eventSource.addEventListener('text', (e) => {
    const data = JSON.parse(e.data);
    console.log('Agent:', data.content);
});

eventSource.addEventListener('tool_use', (e) => {
    const data = JSON.parse(e.data);
    console.log('Using tool:', data.tool);
});

eventSource.addEventListener('message_complete', (e) => {
    console.log('Complete!');
    eventSource.close();
});

eventSource.addEventListener('error', (e) => {
    const data = JSON.parse(e.data);
    console.error('Error:', data.error);
});
```

---

### Cancel Processing

Stop ongoing agent processing.

```http
POST /sessions/{session_id}/cancel
```

**Response:** `200 OK`

```json
{
    "status": "cancelled",
    "message": "Processing cancelled successfully"
}
```

Or if not processing:

```json
{
    "status": "not_processing",
    "message": "No active processing to cancel"
}
```

---

## Health & Configuration

### Health Check

Comprehensive health status.

```http
GET /health
```

**Response:** `200 OK`

```json
{
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2024-12-07T10:30:00Z",
    "checks": {
        "database": {"status": "healthy", "type": "sqlite"},
        "api_key": {"status": "configured", "provider": "anthropic"}
    }
}
```

**Status Values:**
- `healthy` - All systems operational
- `degraded` - Some issues but operational
- `unhealthy` - Critical issues

---

### Readiness Check

Strict readiness probe for orchestrators.

```http
GET /health/ready
```

**Response:** `200 OK`

```json
{
    "status": "ready"
}
```

**Error Response:** `503 Service Unavailable`

```json
{
    "detail": "Database not ready: connection failed"
}
```

---

### Liveness Check

Simple process liveness.

```http
GET /health/live
```

**Response:** `200 OK`

```json
{
    "status": "alive"
}
```

---

### Get Configuration

Non-sensitive configuration information.

```http
GET /config
```

**Response:** `200 OK`

```json
{
    "app_name": "Claude Computer Use Backend",
    "version": "1.0.0",
    "api_provider": "anthropic",
    "default_model": "claude-sonnet-4-5-20250929",
    "vnc_url": "http://localhost:6080/vnc.html",
    "available_providers": ["anthropic", "bedrock", "vertex"]
}
```

---

## Error Responses

All error responses follow this format:

```json
{
    "detail": "Error description"
}
```

Or for validation errors:

```json
{
    "detail": [
        {
            "loc": ["body", "content"],
            "msg": "String should have at least 1 character",
            "type": "string_too_short"
        }
    ]
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `204` | No Content (successful deletion) |
| `400` | Bad Request |
| `404` | Not Found |
| `409` | Conflict (e.g., already processing) |
| `422` | Validation Error |
| `429` | Rate Limited |
| `500` | Internal Server Error |
| `503` | Service Unavailable |

---

## Rate Limiting

Default limits (configurable via environment):

- **Messages:** 10 per minute per session
- **Sessions:** 20 per hour per IP

When rate limited:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

```json
{
    "error": "Rate limit exceeded",
    "detail": "10 per 1 minute",
    "retry_after": 60
}
```

