#!/bin/bash
# ==============================================================================
# Claude Computer Use Backend - Entrypoint Script
# ==============================================================================
#
# Initializes and starts all required services:
# 1. X11 virtual framebuffer (Xvfb)
# 2. Window manager (Mutter)
# 3. VNC server (x11vnc)
# 4. noVNC web interface
# 5. FastAPI backend
# 6. Static file server for frontend
#
# ==============================================================================

set -e

echo "=============================================="
echo "  Claude Computer Use Backend"
echo "=============================================="
echo ""

# ==============================================================================
# Environment Setup
# ==============================================================================

export DISPLAY=:${DISPLAY_NUM:-1}
export HOME=/home/computeruse

cd $HOME

# ==============================================================================
# Start X11/VNC Stack
# ==============================================================================

echo "🖥️  Starting X11 virtual framebuffer..."
./xvfb_startup.sh

echo "🪟 Starting window manager..."
./mutter_startup.sh

echo "📺 Starting VNC server..."
./x11vnc_startup.sh

echo "🌐 Starting noVNC web interface..."
./novnc_startup.sh

# Wait for X11 to be ready
sleep 2

echo "🖥️  Starting taskbar..."
./tint2_startup.sh

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
echo "  🖼️  VNC:       http://localhost:6080/vnc.html"
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

