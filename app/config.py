"""
Application Configuration
=========================

Centralized configuration management using Pydantic Settings.
All sensitive values are loaded from environment variables.

Usage:
    from app.config import settings
    api_key = settings.anthropic_api_key.get_secret_value()
"""

import os
from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables or .env file.
    Sensitive values use SecretStr to prevent accidental exposure in logs.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ==========================================================================
    # API Configuration
    # ==========================================================================
    
    app_name: str = "DeskCloud MCP"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # API prefix for all routes
    api_v1_prefix: str = "/api/v1"
    
    # ==========================================================================
    # Anthropic API Configuration
    # ==========================================================================
    
    # API key for Claude - REQUIRED
    anthropic_api_key: SecretStr = SecretStr("")
    
    # API provider: anthropic, bedrock, or vertex
    api_provider: Literal["anthropic", "bedrock", "vertex"] = "anthropic"
    
    # Default model to use for new sessions
    default_model: str = "claude-sonnet-4-5-20250929"
    
    # Maximum output tokens (default for Claude 4.5)
    max_output_tokens: int = 16384
    
    # ==========================================================================
    # Database Configuration
    # ==========================================================================
    
    # SQLite for development, PostgreSQL for production
    database_url: str = "sqlite+aiosqlite:///./data/sessions.db"
    
    # Echo SQL queries (useful for debugging)
    database_echo: bool = False
    
    # ==========================================================================
    # VNC Configuration
    # ==========================================================================
    
    # Screen dimensions for virtual displays
    screen_width: int = 1024
    screen_height: int = 768
    
    # VNC server base port (display :N uses port vnc_base_port + N)
    vnc_base_port: int = 5900
    
    # noVNC web interface base port (display :N uses port novnc_base_port + N)
    novnc_base_port: int = 6080
    
    # Hostname for VNC URLs (used in session responses)
    vnc_host: str = "localhost"
    
    # Legacy VNC URL (for single-display mode, kept for backwards compatibility)
    vnc_base_url: str = "http://localhost:6080/vnc.html"
    
    # Maximum concurrent displays (0 = unlimited)
    max_displays: int = 20
    
    # ==========================================================================
    # Session TTL & Cleanup
    # ==========================================================================
    
    # Session time-to-live in seconds (default: 1 hour)
    session_ttl_seconds: int = 3600
    
    # Cleanup check interval in seconds (default: 5 minutes)
    cleanup_interval_seconds: int = 300
    
    # Extended TTL for authenticated users (future use)
    extended_ttl_seconds: int = 86400  # 24 hours
    
    # ==========================================================================
    # Filesystem Isolation Configuration
    # ==========================================================================
    
    # Base directory for session filesystems
    sessions_dir: str = "/sessions"
    
    # Base filesystem template (read-only layer for OverlayFS)
    filesystem_base_dir: str = "/sessions/base"
    
    # Enable filesystem isolation (requires OverlayFS or falls back to copy)
    filesystem_isolation_enabled: bool = True
    
    # Per-session disk quota in MB (0 = unlimited)
    session_disk_quota_mb: int = 500
    
    # ==========================================================================
    # MCP Server Configuration
    # ==========================================================================
    
    # Enable MCP server
    mcp_enabled: bool = True
    
    # ==========================================================================
    # Rate Limiting
    # ==========================================================================
    
    # Messages per minute per session
    rate_limit_messages: str = "10/minute"
    
    # Sessions per hour per IP
    rate_limit_sessions: str = "20/hour"
    
    # ==========================================================================
    # CORS Configuration
    # ==========================================================================
    
    # Allowed origins (comma-separated in env, parsed to list)
    cors_origins: str = "http://localhost:8080,http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # ==========================================================================
    # Validators
    # ==========================================================================
    
    @field_validator("anthropic_api_key", mode="before")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Warn if API key is not set (but allow empty for testing)."""
        if not v:
            # Try to get from environment directly (for Docker scenarios)
            v = os.getenv("ANTHROPIC_API_KEY", "")
        return v


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures settings are only loaded once,
    improving performance and preventing repeated file reads.
    """
    return Settings()


# Global settings instance for convenient imports
settings = get_settings()

