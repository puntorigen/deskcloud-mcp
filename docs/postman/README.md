# Postman Collection

**Author:** Pablo Schaffner

Ready-to-use Postman collection for testing and demonstrating the Claude Computer Use API.

---

## 📦 Files

| File | Description |
|------|-------------|
| `claude-computer-use-api.postman_collection.json` | Complete API collection |
| `claude-computer-use-api.postman_environment.json` | Environment variables |

---

## 🚀 Quick Start

### 1. Import into Postman

1. Open Postman
2. Click **Import** (top left)
3. Drag both JSON files or browse to select them
4. Click **Import**

### 2. Select Environment

1. In the top-right corner, click the environment dropdown
2. Select **"🖥️ Claude Computer Use - Local"**

### 3. Start the Backend

```bash
cd computer-use-backend
docker-compose up
```

### 4. Run Tests

1. Open the collection in Postman
2. Start with **Health Check** to verify connectivity
3. Run **Create Session** to get a session ID
4. Try **Send Message** to interact with the agent

---

## 📁 Collection Structure

```
🖥️ Claude Computer Use API
├── 🏥 Health & Status
│   ├── Health Check
│   ├── Readiness Probe
│   ├── Liveness Probe
│   └── Get Configuration
├── 📋 Sessions
│   ├── Create Session
│   ├── Create Session (with Custom Prompt)
│   ├── Create Session (Minimal)
│   ├── List Sessions
│   ├── Get Session
│   └── Delete Session
├── 💬 Messages
│   ├── Send Message
│   ├── Send Message (Simple Task)
│   ├── Send Message (Complex Task)
│   ├── Cancel Processing
│   └── Stream Events (SSE) ⚡
└── 🧪 Test Scenarios
    ├── 🎬 Demo Flow: Weather Search
    │   ├── 1. Create Demo Session
    │   ├── 2. Search Weather
    │   └── 3. Get Results
    └── 🔄 Full CRUD Test
        ├── 1. List Initial Sessions
        ├── 2. Create Test Session
        ├── 3. Verify Created
        ├── 4. Delete Session
        └── 5. Verify Deleted
```

---

## 🧪 Test Features

Every request includes:

- ✅ **Response validation tests**
- ✅ **Auto-populated variables** (session_id, message_id)
- ✅ **Example responses**
- ✅ **Detailed descriptions**

### Running All Tests

1. Right-click on the collection
2. Select **"Run collection"**
3. Click **"Run Claude Computer Use API"**

---

## 📺 Demo Video Tips

### Recommended Demo Flow

1. **Health Check** → Show system is healthy
2. **Get Configuration** → Show available providers
3. **Create Session** → Create a demo session
4. **Open VNC** → Show the virtual desktop (`http://localhost:6080`)
5. **Send Message** → "Search for weather in Tokyo"
6. **Watch VNC** → See the agent control Firefox
7. **Get Session** → Show chat history with tool usage

### SSE Streaming Demo

The SSE endpoint doesn't work well in Postman. For the demo, use the browser console:

```javascript
// Open browser developer tools → Console
const es = new EventSource('http://localhost:8000/api/v1/sessions/YOUR_SESSION_ID/stream');

es.addEventListener('text', (e) => {
    console.log('🤖', JSON.parse(e.data).content);
});

es.addEventListener('tool_use', (e) => {
    console.log('🔧', JSON.parse(e.data).tool);
});

es.addEventListener('message_complete', () => {
    console.log('✅ Complete!');
    es.close();
});
```

---

## 🔧 Customization

### Change Base URL

Edit the environment variable `base_url`:

- Local: `http://localhost:8000`
- Docker: `http://docker-host:8000`
- Production: `https://your-domain.com`

### Add Authentication (Future)

If auth is added, update collection pre-request script:

```javascript
pm.request.headers.add({
    key: 'Authorization',
    value: 'Bearer ' + pm.environment.get('api_token')
});
```

---

## 📝 Notes

- **SSE endpoints** require browser/curl testing
- **session_id** is auto-saved after creating a session
- **Delete** is soft-delete (archive)
- Tests assume fresh database state

---

*Happy testing! 🚀*

