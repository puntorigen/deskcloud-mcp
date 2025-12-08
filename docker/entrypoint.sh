#!/bin/bash
# ==============================================================================
# Claude Computer Use Backend - Entrypoint Script
# ==============================================================================
#
# Multi-Session Architecture:
# ---------------------------
# X11/VNC services are now managed dynamically by the DisplayManager service.
# Each session gets its own isolated display created on demand:
# - Session 1 → DISPLAY=:1, VNC port 5901, noVNC port 6081
# - Session 2 → DISPLAY=:2, VNC port 5902, noVNC port 6082
# - etc.
#
# This script only starts:
# 1. Database initialization
# 2. FastAPI backend (which includes DisplayManager)
# 3. Static file server for frontend
#
# ==============================================================================

set -e

echo "=============================================="
echo "  Claude Computer Use Backend"
echo "  Multi-Session Architecture"
echo "=============================================="
echo ""

# ==============================================================================
# Environment Setup
# ==============================================================================

export HOME=/home/computeruse

cd $HOME

# ==============================================================================
# NOTE: X11/VNC services are now created per-session by DisplayManager
# ==============================================================================

echo "ℹ️  X11/VNC services will be created per-session by DisplayManager"
echo "   Each session gets an isolated DISPLAY and VNC port"
echo ""

# ==============================================================================
# Initialize Database
# ==============================================================================

echo "🗄️  Initializing database..."
mkdir -p /home/computeruse/data
python -c "from app.db.session import init_db_sync; init_db_sync()"

# ==============================================================================
# Start Application Services
# ==============================================================================

echo "🚀 Starting FastAPI backend..."
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info \
    > /tmp/fastapi.log 2>&1 &

# Wait for FastAPI to start
sleep 2

echo "📁 Starting frontend server..."
python -m http.server 8080 \
    --directory /home/computeruse/frontend \
    > /tmp/frontend.log 2>&1 &

# ==============================================================================
# Startup Complete
# ==============================================================================

echo ""
echo "=============================================="
echo "  ✅ All services started!"
echo "=============================================="
echo ""
echo "  📡 API:       http://localhost:8000"
echo "  📝 API Docs:  http://localhost:8000/docs"
echo "  🖥️  Frontend:  http://localhost:8080"
echo ""
echo "  Multi-Session Mode:"
echo "  -------------------"
echo "  Each session gets its own VNC port:"
echo "  - Session 1: http://localhost:6081/vnc.html"
echo "  - Session 2: http://localhost:6082/vnc.html"
echo "  - etc."
echo ""
echo "  The vnc_url in API responses shows the correct URL"
echo "  for each session's isolated desktop."
echo ""
echo "  Set ANTHROPIC_API_KEY environment variable"
echo "  to enable agent functionality."
echo ""
echo "=============================================="

# ==============================================================================
# Keep Container Running
# ==============================================================================

# Tail logs for debugging (shows both FastAPI and frontend logs)
tail -f /tmp/fastapi.log /tmp/frontend.log &

# Keep the container running
wait

