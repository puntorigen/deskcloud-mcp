"""
Bash tool for executing shell commands.

Forked from Anthropic's computer-use-demo with modifications for
per-session environment isolation. Key changes:
- __init__ accepts env dict parameter
- Bash subprocess uses session-specific environment
"""

import asyncio
import os
from typing import Any, Literal

from .base import BaseAnthropicTool, CLIResult, ToolError, ToolResult


class _BashSession:
    """
    A session of a bash shell.
    
    MODIFIED: Accepts env dict for per-session isolation.
    """

    _started: bool
    _process: asyncio.subprocess.Process
    _env: dict[str, str] | None

    command: str = "/bin/bash"
    _output_delay: float = 0.2  # seconds
    _timeout: float = 120.0  # seconds
    _sentinel: str = "<<exit>>"

    def __init__(self, env: dict[str, str] | None = None):
        """
        Initialize bash session with optional environment.
        
        Args:
            env: Session-specific environment dict containing:
                 - HOME: Isolated home directory
                 - TMPDIR: Isolated temp directory
                 - DISPLAY: X11 display for GUI apps
                 - XDG_* variables for proper app isolation
        """
        self._started = False
        self._timed_out = False
        self._env = env

    def _get_env(self) -> dict[str, str]:
        """Get environment dict for subprocess."""
        if self._env is not None:
            # Merge with current os.environ but override with session env
            env = os.environ.copy()
            env.update(self._env)
            return env
        return dict(os.environ)

    async def start(self):
        if self._started:
            return

        # MODIFIED: Pass session environment to subprocess
        self._process = await asyncio.create_subprocess_shell(
            self.command,
            preexec_fn=os.setsid,
            shell=True,
            bufsize=0,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._get_env(),  # Use session-specific environment
        )

        self._started = True

    def stop(self):
        """Terminate the bash shell."""
        if not self._started:
            raise ToolError("Session has not started.")
        if self._process.returncode is not None:
            return
        self._process.terminate()

    async def run(self, command: str):
        """Execute a command in the bash shell."""
        if not self._started:
            raise ToolError("Session has not started.")
        if self._process.returncode is not None:
            return ToolResult(
                system="tool must be restarted",
                error=f"bash has exited with returncode {self._process.returncode}",
            )
        if self._timed_out:
            raise ToolError(
                f"timed out: bash has not returned in {self._timeout} seconds and must be restarted",
            )

        assert self._process.stdin
        assert self._process.stdout
        assert self._process.stderr

        # send command to the process
        self._process.stdin.write(
            command.encode() + f"; echo '{self._sentinel}'\n".encode()
        )
        await self._process.stdin.drain()

        # read output from the process, until the sentinel is found
        try:
            async with asyncio.timeout(self._timeout):
                while True:
                    await asyncio.sleep(self._output_delay)
                    output = self._process.stdout._buffer.decode()  # pyright: ignore[reportAttributeAccessIssue]
                    if self._sentinel in output:
                        output = output[: output.index(self._sentinel)]
                        break
        except asyncio.TimeoutError:
            self._timed_out = True
            raise ToolError(
                f"timed out: bash has not returned in {self._timeout} seconds and must be restarted",
            ) from None

        if output.endswith("\n"):
            output = output[:-1]

        error = self._process.stderr._buffer.decode()  # pyright: ignore[reportAttributeAccessIssue]
        if error.endswith("\n"):
            error = error[:-1]

        # clear the buffers so that the next output can be read correctly
        self._process.stdout._buffer.clear()  # pyright: ignore[reportAttributeAccessIssue]
        self._process.stderr._buffer.clear()  # pyright: ignore[reportAttributeAccessIssue]

        return CLIResult(output=output, error=error)


class BashTool20250124(BaseAnthropicTool):
    """
    A tool that allows the agent to run bash commands.
    
    MODIFIED: Accepts env dict for per-session isolation.
    """

    _session: _BashSession | None
    _env: dict[str, str] | None

    api_type: Literal["bash_20250124"] = "bash_20250124"
    name: Literal["bash"] = "bash"

    def __init__(self, env: dict[str, str] | None = None):
        """
        Initialize BashTool with optional session-specific environment.
        
        Args:
            env: Session-specific environment dict. Should contain:
                 - HOME: Isolated home directory  
                 - TMPDIR: Isolated temp directory
                 - DISPLAY: X11 display for GUI apps
                 - XDG_* variables for proper app isolation
        """
        self._session = None
        self._env = env
        super().__init__()

    def to_params(self) -> Any:
        return {
            "type": self.api_type,
            "name": self.name,
        }

    async def __call__(
        self, command: str | None = None, restart: bool = False, **kwargs
    ):
        if restart:
            if self._session:
                self._session.stop()
            # MODIFIED: Pass env to bash session
            self._session = _BashSession(env=self._env)
            await self._session.start()

            return ToolResult(system="tool has been restarted.")

        if self._session is None:
            # MODIFIED: Pass env to bash session
            self._session = _BashSession(env=self._env)
            await self._session.start()

        if command is not None:
            return await self._session.run(command)

        raise ToolError("no command provided.")


class BashTool20241022(BashTool20250124):
    api_type: Literal["bash_20250124"] = "bash_20250124"  # pyright: ignore[reportIncompatibleVariableOverride]


# Alias for convenience
BashTool = BashTool20250124
