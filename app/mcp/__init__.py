"""
MCP Server Module
=================

Model Context Protocol (MCP) server implementation for Claude Computer Use.

This module exposes computer-use capabilities as MCP tools that can be
consumed by AI assistants like Cursor IDE or Claude Desktop.

Exports:
    mcp_server: FastMCP server instance with all tools registered
    create_mcp_app: Function to create Starlette app for mounting
"""

from .server import create_mcp_app, mcp_server

__all__ = ["mcp_server", "create_mcp_app"]
