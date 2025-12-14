#!/bin/bash
# ==============================================================================
# DeskCloud MCP - Entrypoint Script
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
echo "  DeskCloud MCP"
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

echo "🗄️  Database will be initialized on app startup..."
mkdir -p /home/computeruse/data
# Skip separate init - the app's lifespan handler initializes the database

# ==============================================================================
# Initialize Filesystem Isolation
# ==============================================================================

if [ "${FILESYSTEM_ISOLATION_ENABLED:-true}" = "true" ]; then
    echo "📁 Initializing filesystem isolation..."
    
    # Ensure sessions directories exist with proper structure
    mkdir -p /sessions/base/home/user/.config
    mkdir -p /sessions/base/home/user/.local/share
    mkdir -p /sessions/base/home/user/.cache
    mkdir -p /sessions/base/home/user/Desktop
    mkdir -p /sessions/base/home/user/Downloads
    mkdir -p /sessions/base/tmp
    mkdir -p /sessions/active
    mkdir -p /sessions/snapshots
    chmod 1777 /sessions/base/tmp
    
    # Ensure OverlayFS kernel module is loaded
    if ! grep -q overlay /proc/filesystems 2>/dev/null; then
        echo "🔧 Loading overlay kernel module..."
        modprobe overlay 2>/dev/null || true
    fi
    
    # Verify OverlayFS kernel module is loaded
    if ! grep -q overlay /proc/filesystems 2>/dev/null; then
        echo "⚠️  OverlayFS module not loaded, this is unusual..."
        echo "   Docker uses OverlayFS internally, so it should always be available"
    else
        echo "✅ OverlayFS kernel module is loaded"
    fi
    
    # Test if we can actually mount overlayfs (requires CAP_SYS_ADMIN)
    TEST_DIR="/tmp/.overlay_test_$$"
    mkdir -p "$TEST_DIR"/{lower,upper,work,merged}
    
    if mount -t overlay overlay \
        -o "lowerdir=$TEST_DIR/lower,upperdir=$TEST_DIR/upper,workdir=$TEST_DIR/work" \
        "$TEST_DIR/merged" 2>/dev/null; then
        umount "$TEST_DIR/merged" 2>/dev/null
        rm -rf "$TEST_DIR"
        echo "✅ OverlayFS mount permissions OK"
    else
        rm -rf "$TEST_DIR"
        echo ""
        echo "❌ ERROR: Cannot mount OverlayFS!"
        echo ""
        echo "   This is a PERMISSIONS issue, not a missing package."
        echo "   OverlayFS is a kernel feature (not installable separately)."
        echo ""
        echo "   Fix: Add these to docker-compose.yml:"
        echo ""
        echo "     services:"
        echo "       app:"
        echo "         cap_add:"
        echo "           - SYS_ADMIN"
        echo "         security_opt:"
        echo "           - apparmor:unconfined"
        echo ""
        exit 1
    fi
else
    echo "ℹ️  Filesystem isolation disabled"
fi

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
echo "  Each session gets:"
echo "  - Isolated X11 display (VNC port 6081, 6082, ...)"
echo "  - Isolated filesystem (HOME, downloads, configs)"
echo ""
echo "  Session isolation:"
echo "  - Display:    http://localhost:6081/vnc.html (per session)"
echo "  - Filesystem: OverlayFS with CoW (copy-on-write)"
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

