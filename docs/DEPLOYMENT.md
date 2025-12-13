# Deployment Guide

**Author:** Pablo Schaffner

Instructions for deploying DeskCloud MCP in various environments.

## Table of Contents

- [Local Docker](#local-docker)
- [Production Considerations](#production-considerations)
- [Render.com Deployment](#rendercom-deployment)
- [Environment Variables](#environment-variables)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Local Docker

### Quick Start

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# 2. Build and run
docker-compose up --build

# 3. Access
# Frontend: http://localhost:8080
# API:      http://localhost:8000
# VNC:      http://localhost:6080/vnc.html
```

### Production Mode

```bash
# Run in background with restart policy
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Resource Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 2 GB | 4 GB |
| Disk | 1 GB | 5 GB |

---

## Production Considerations

### Security Checklist

- [ ] Set strong `ANTHROPIC_API_KEY` and keep it secret
- [ ] Restrict `CORS_ORIGINS` to your domain only
- [ ] Enable HTTPS via reverse proxy (nginx, Traefik)
- [ ] Set `DEBUG=false`
- [ ] Consider adding authentication layer
- [ ] Implement rate limiting (already included)
- [ ] Restrict network access from agent container

### Database

For production with multiple users, switch to PostgreSQL:

```bash
# docker-compose.yml addition
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: computeruse
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  app:
    environment:
      DATABASE_URL: postgresql+asyncpg://app:${DB_PASSWORD}@db:5432/computeruse
    depends_on:
      - db
```

### Scaling

The current architecture is single-instance due to VNC requirements. For multiple concurrent users:

1. **Container per Session** - Spin up a new container for each active session
2. **Orchestration** - Use Kubernetes or ECS for container management
3. **Shared State** - Use Redis for session state coordination
4. **Load Balancer** - Route based on session ID

---

## Render.com Deployment

Render.com can host this application with some modifications.

### Prerequisites

1. GitHub repository with the code
2. Render.com account
3. Anthropic API key

### Configuration Files

Create `Dockerfile.render` for single-port architecture:

```dockerfile
FROM ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest

USER root
RUN apt-get update && apt-get install -y nginx && apt-get clean

USER computeruse
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=computeruse:computeruse app/ /home/computeruse/app/
COPY --chown=computeruse:computeruse frontend/ /home/computeruse/frontend/
COPY --chown=computeruse:computeruse nginx.render.conf /etc/nginx/nginx.conf
COPY --chown=computeruse:computeruse entrypoint.render.sh /home/computeruse/entrypoint.sh
RUN chmod +x /home/computeruse/entrypoint.sh

ENV PORT=10000
EXPOSE 10000

ENTRYPOINT ["/home/computeruse/entrypoint.sh"]
```

Create `nginx.render.conf`:

```nginx
events { worker_connections 1024; }

http {
    include /etc/nginx/mime.types;
    
    upstream fastapi { server 127.0.0.1:8000; }
    upstream novnc { server 127.0.0.1:6080; }
    
    server {
        listen 10000;
        
        location / {
            root /home/computeruse/frontend;
            try_files $uri $uri/ /index.html;
        }
        
        location /api/ {
            proxy_pass http://fastapi;
            proxy_http_version 1.1;
            proxy_set_header Connection '';
            proxy_buffering off;
            proxy_read_timeout 86400s;
        }
        
        location /vnc/ {
            proxy_pass http://novnc/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        
        location /websockify {
            proxy_pass http://novnc;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

Create `render.yaml`:

```yaml
services:
  - type: web
    name: deskcloud-mcp
    runtime: docker
    dockerfilePath: ./Dockerfile.render
    plan: standard
    healthCheckPath: /api/v1/health
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: DATABASE_URL
        value: sqlite+aiosqlite:////data/sessions.db
    disk:
      name: data
      mountPath: /data
      sizeGB: 1
```

### Deployment Steps

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect repository
4. Set `ANTHROPIC_API_KEY` in environment variables
5. Select **Standard** plan (minimum 2GB RAM)
6. Add persistent disk
7. Deploy

### Access URLs

After deployment:
- Frontend: `https://your-app.onrender.com/`
- API: `https://your-app.onrender.com/api/v1/`
- VNC: `https://your-app.onrender.com/vnc/vnc.html`

### Cost

| Render Plan | RAM | Monthly Cost |
|-------------|-----|--------------|
| Free | 512MB | $0 (not suitable) |
| Starter | 512MB | $7 (not suitable) |
| **Standard** | 2GB | $25 (minimum) |
| Pro | 4GB | $85 (recommended) |

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `API_PROVIDER` | API provider | `anthropic` |
| `DATABASE_URL` | Database connection | `sqlite+aiosqlite:///./data/sessions.db` |
| `DEBUG` | Enable debug mode | `false` |
| `CORS_ORIGINS` | Allowed origins | `http://localhost:8080` |
| `DEFAULT_MODEL` | Default Claude model | `claude-sonnet-4-5-20250929` |
| `VNC_BASE_URL` | VNC viewer URL | `http://localhost:6080/vnc.html` |
| `DISPLAY_NUM` | X11 display number | `1` |
| `WIDTH` | Screen width | `1024` |
| `HEIGHT` | Screen height | `768` |

---

## Monitoring

### Health Checks

```bash
# Comprehensive health
curl http://localhost:8000/api/v1/health

# Readiness (for load balancers)
curl http://localhost:8000/api/v1/health/ready

# Liveness (for container orchestration)
curl http://localhost:8000/api/v1/health/live
```

### Docker Health Check

Already configured in Dockerfile:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1
```

### Logs

```bash
# All logs
docker-compose logs -f

# Just app logs
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app
```

### Metrics (Future)

For production monitoring, consider adding:

- **Prometheus** - Metrics collection
- **Grafana** - Visualization
- **Sentry** - Error tracking

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs app

# Common issues:
# - API key not set: Set ANTHROPIC_API_KEY
# - Port conflict: Change ports in docker-compose.yml
# - Permission denied: Check file ownership
```

### VNC Not Working

```bash
# Check X11 processes
docker-compose exec app ps aux | grep -E "Xvfb|x11vnc"

# Check VNC logs
docker-compose exec app cat /tmp/x11vnc.log
```

### API Returns 503

```bash
# Check health
curl http://localhost:8000/api/v1/health

# Common causes:
# - API key not configured
# - Database connection failed
```

### SSE Connection Drops

- Increase proxy timeouts
- Check for buffering issues
- Ensure `X-Accel-Buffering: no` header

### Database Errors

```bash
# Reset database
rm -rf data/sessions.db
docker-compose restart app
```

### Memory Issues

```bash
# Check memory usage
docker stats

# Increase limits in docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 4G
```

---

## Backup & Recovery

### Database Backup

```bash
# SQLite
cp data/sessions.db data/sessions.db.backup

# PostgreSQL
docker-compose exec db pg_dump -U app computeruse > backup.sql
```

### Restore

```bash
# SQLite
cp data/sessions.db.backup data/sessions.db

# PostgreSQL
docker-compose exec -T db psql -U app computeruse < backup.sql
```

