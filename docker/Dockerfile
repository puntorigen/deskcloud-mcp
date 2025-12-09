# ==============================================================================
# Claude Computer Use Backend - Dockerfile
# ==============================================================================
#
# Extends the Anthropic Computer Use demo image with:
# - FastAPI backend instead of Streamlit
# - Custom frontend
# - Session persistence
#
# Build:
#   docker build -f docker/Dockerfile -t claude-computer-use-backend .
#
# Run:
#   docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY -p 8000:8000 -p 6080:6080 claude-computer-use-backend
#
# ==============================================================================

# Use the official Anthropic Computer Use demo as base
# This provides: Ubuntu 22.04, Python 3.11, X11/VNC stack, Firefox, tools
FROM ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest

# Labels for image metadata
LABEL maintainer="Principal AI Specialist"
LABEL description="Claude Computer Use Backend with FastAPI and session management"
LABEL version="1.0.0"

# ==============================================================================
# Install Additional Dependencies
# ==============================================================================

USER root

# Install nginx for reverse proxy and zstd for filesystem snapshots
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    zstd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to non-root user
USER computeruse
WORKDIR /home/computeruse

# ==============================================================================
# Install Python Dependencies
# ==============================================================================

# Copy requirements first for better caching
COPY --chown=computeruse:computeruse requirements.txt /tmp/requirements.txt

# Install our backend dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ==============================================================================
# Copy Application Code
# ==============================================================================

# Copy backend application
COPY --chown=computeruse:computeruse app/ /home/computeruse/app/

# Copy frontend
COPY --chown=computeruse:computeruse frontend/ /home/computeruse/frontend/

# Copy entrypoint script
COPY --chown=computeruse:computeruse docker/entrypoint.sh /home/computeruse/entrypoint.sh
RUN chmod +x /home/computeruse/entrypoint.sh

# ==============================================================================
# Environment Configuration
# ==============================================================================

# Display settings (inherited from base, can be overridden)
ENV DISPLAY_NUM=1
ENV WIDTH=1024
ENV HEIGHT=768

# Application settings
ENV PYTHONPATH=/home/computeruse
ENV PYTHONUNBUFFERED=1

# Database (SQLite by default, can be overridden to PostgreSQL)
ENV DATABASE_URL=sqlite+aiosqlite:///./data/sessions.db

# Filesystem isolation settings
ENV SESSIONS_DIR=/sessions
ENV FILESYSTEM_BASE_DIR=/sessions/base
ENV FILESYSTEM_ISOLATION_ENABLED=true

# Create data directory for SQLite
RUN mkdir -p /home/computeruse/data

# Create sessions directory structure for filesystem isolation
# This needs to be done as root for OverlayFS support
USER root
RUN mkdir -p /sessions/base/home/user/.config \
    && mkdir -p /sessions/base/home/user/.local/share \
    && mkdir -p /sessions/base/home/user/.cache \
    && mkdir -p /sessions/base/home/user/Desktop \
    && mkdir -p /sessions/base/home/user/Downloads \
    && mkdir -p /sessions/base/tmp \
    && mkdir -p /sessions/active \
    && mkdir -p /sessions/snapshots \
    && chmod 1777 /sessions/base/tmp \
    && chown -R computeruse:computeruse /sessions
USER computeruse

# ==============================================================================
# Ports
# ==============================================================================

# FastAPI backend
EXPOSE 8000

# Frontend static server
EXPOSE 8080

# noVNC web interface
EXPOSE 6080

# Direct VNC connection
EXPOSE 5900

# ==============================================================================
# Health Check
# ==============================================================================

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# ==============================================================================
# Entrypoint
# ==============================================================================

ENTRYPOINT ["/home/computeruse/entrypoint.sh"]

