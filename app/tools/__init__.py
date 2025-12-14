"""
Forked Anthropic tools with per-session environment isolation.

This module contains modified versions of Anthropic's computer-use-demo tools
that accept an `env` parameter for per-session isolation in multi-tenant
environments.

Key modifications:
- All tools accept `env: dict[str, str] | None` in constructor
- Subprocess calls use session-specific environment
- No global os.environ modification (prevents race conditions)
"""

from .base import BaseAnthropicTool, CLIResult, ToolError, ToolFailure, ToolResult
from .bash import BashTool, BashTool20241022, BashTool20250124
from .collection import ToolCollection
from .computer import (
    ComputerTool,
    ComputerTool20241022,
    ComputerTool20250124,
    ComputerTool20251124,
)
from .edit import EditTool, EditTool20241022, EditTool20250124, EditTool20250728
from .groups import TOOL_GROUPS_BY_VERSION, ToolGroup, ToolVersion

__all__ = [
    # Base
    "BaseAnthropicTool",
    "CLIResult",
    "ToolError",
    "ToolFailure",
    "ToolResult",
    # Tools
    "BashTool",
    "BashTool20241022",
    "BashTool20250124",
    "ComputerTool",
    "ComputerTool20241022",
    "ComputerTool20250124",
    "ComputerTool20251124",
    "EditTool",
    "EditTool20241022",
    "EditTool20250124",
    "EditTool20250728",
    # Collection
    "ToolCollection",
    # Groups
    "TOOL_GROUPS_BY_VERSION",
    "ToolGroup",
    "ToolVersion",
]
