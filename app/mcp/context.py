"""
MCP Request Context
===================

Context variables for passing request-scoped data through the MCP stack.
This enables BYOK (Bring Your Own Key) where users provide their API key
via HTTP headers rather than tool parameters.

The key insight is that API keys should NEVER flow through the LLM -
they should only flow through infrastructure (HTTP headers, middleware).
"""

from contextvars import ContextVar
from typing import Optional

# =============================================================================
# Context Variable for API Key (BYOK Support)
# =============================================================================

# This context variable holds the API key for the current request
# It's set by middleware and read by tools
_current_api_key: ContextVar[Optional[str]] = ContextVar("current_api_key", default=None)


def get_current_api_key() -> Optional[str]:
    """
    Get the API key for the current request (BYOK).
    
    Returns:
        API key from X-Anthropic-API-Key header, or None if not provided
    """
    return _current_api_key.get()


def set_current_api_key(api_key: Optional[str]) -> None:
    """
    Set the API key for the current request.
    
    Called by middleware when processing incoming requests.
    """
    _current_api_key.set(api_key)


class APIKeyToken:
    """Token for resetting the API key context variable."""
    
    def __init__(self, token):
        self._token = token
    
    def reset(self):
        _current_api_key.reset(self._token)


def set_current_api_key_with_reset(api_key: Optional[str]) -> APIKeyToken:
    """
    Set the API key and return a token for resetting.
    
    Use in try/finally blocks:
        token = set_current_api_key_with_reset(key)
        try:
            ...
        finally:
            token.reset()
    """
    token = _current_api_key.set(api_key)
    return APIKeyToken(token)



