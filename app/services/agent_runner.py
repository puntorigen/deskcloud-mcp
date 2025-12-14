"""
Agent Runner Service
====================

Wraps the sampling_loop with callbacks that emit events to an async queue
for SSE streaming.

This is the bridge between our forked tools and the FastAPI backend.
The key improvement is that each session gets its own isolated tools
with session-specific environment (no global os.environ modification).

Architecture:
    1. AgentRunner receives user message and session context
    2. Creates ToolCollection with session-specific environment
    3. Spawns background task running sampling_loop with pre-built tools
    4. Callbacks push Event objects to queue
    5. SSE endpoint consumes queue and streams to client
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.config import settings
from app.core.events import (
    Event,
    EventType,
    create_event,
    error_event,
    keepalive_event,
    message_complete_event,
    text_event,
    thinking_event,
    tool_result_event,
    tool_use_event,
)

# Import our forked tools with per-session environment support
from app.tools import (
    BashTool,
    ComputerTool,
    EditTool,
    ToolCollection,
    ToolResult,
)
from app.tools.loop import APIProvider, sampling_loop
from app.tools.groups import ToolVersion, TOOL_GROUPS_BY_VERSION


@dataclass
class AgentRunner:
    """
    Orchestrates agent execution with event streaming and per-session isolation.
    
    Each AgentRunner creates tools with session-specific environment variables,
    ensuring complete isolation between sessions (no race conditions).
    
    Attributes:
        session_id: Current session identifier
        model: Claude model to use
        provider: API provider (anthropic, bedrock, vertex)
        api_key: API key for the provider
        system_prompt_suffix: Custom instructions
        messages: Conversation history (mutable - updated by loop)
        session_env: Session-specific environment (DISPLAY, HOME, TMPDIR, etc.)
        event_queue: Queue for streaming events to SSE
        _task: Background task running the agent loop
        _tool_collection: Pre-built tools with session environment
    
    Example:
        runner = AgentRunner(
            session_id="sess_123",
            model="claude-sonnet-4-5-20250929",
            messages=[],
            session_env={
                "DISPLAY": ":5",
                "DISPLAY_NUM": "5",
                "WIDTH": "1024",
                "HEIGHT": "768",
                "HOME": "/sessions/active/sess_123/merged/home/user",
                "TMPDIR": "/sessions/active/sess_123/merged/tmp",
            },
        )
        queue = await runner.run("Search the weather in Santiago, Chile")
        
        async for event in runner.iter_events():
            yield event.to_sse()
    """
    
    session_id: str
    model: str
    provider: str = "anthropic"
    api_key: str = ""
    system_prompt_suffix: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    tool_version: str = "computer_use_20250124"
    max_tokens: int = 16384
    thinking_budget: int | None = None
    session_env: dict[str, str] | None = None  # Session-specific environment
    
    # Internal state
    event_queue: asyncio.Queue[Event] = field(default_factory=asyncio.Queue)
    _task: asyncio.Task | None = field(default=None, repr=False)
    _message_id: str = field(default="", repr=False)
    _tool_collection: ToolCollection | None = field(default=None, repr=False)
    
    def __post_init__(self):
        """Initialize API key and tool collection."""
        if not self.api_key:
            self.api_key = settings.anthropic_api_key.get_secret_value()
        
        # Create tool collection with session-specific environment
        self._tool_collection = self._create_tool_collection()
    
    def _create_tool_collection(self) -> ToolCollection:
        """
        Create a ToolCollection with session-specific environment.
        
        Each tool receives the session_env dict which is used for all
        subprocess calls, ensuring complete isolation between sessions.
        """
        env = self.session_env or {}
        
        # Create tools with session environment
        computer_tool = ComputerTool(env=env)
        bash_tool = BashTool(env=env)
        edit_tool = EditTool(env=env)
        
        return ToolCollection(computer_tool, bash_tool, edit_tool)
    
    # =========================================================================
    # Callbacks for sampling_loop
    # =========================================================================
    
    def _output_callback(self, content_block: dict[str, Any]) -> None:
        """
        Callback invoked for each content block from Claude.
        
        Handles:
        - Text responses (type: "text")
        - Thinking blocks (type: "thinking")
        - Tool use requests (type: "tool_use")
        """
        block_type = content_block.get("type", "unknown")
        
        if block_type == "text":
            text_content = content_block.get("text", "")
            if text_content:
                event = text_event(text_content, self._message_id)
                self._queue_event(event)
                
        elif block_type == "thinking":
            thinking_content = content_block.get("thinking", "")
            if thinking_content:
                event = thinking_event(thinking_content, self._message_id)
                self._queue_event(event)
                
        elif block_type == "tool_use":
            event = tool_use_event(
                tool_name=content_block.get("name", "unknown"),
                tool_input=content_block.get("input", {}),
                tool_use_id=content_block.get("id", ""),
                message_id=self._message_id,
            )
            self._queue_event(event)
    
    def _tool_output_callback(self, result: ToolResult, tool_use_id: str) -> None:
        """
        Callback invoked after tool execution completes.
        """
        event = tool_result_event(
            tool_use_id=tool_use_id,
            output=getattr(result, 'output', None),
            error=getattr(result, 'error', None),
            screenshot=getattr(result, 'base64_image', None),
            message_id=self._message_id,
        )
        self._queue_event(event)
    
    def _api_response_callback(
        self,
        request: httpx.Request,
        response: httpx.Response | object | None,
        error: Exception | None,
    ) -> None:
        """
        Callback for API response logging/debugging.
        """
        if error:
            err_event = error_event(
                error=str(error),
                code=type(error).__name__,
                message_id=self._message_id,
            )
            self._queue_event(err_event)
    
    def _queue_event(self, event: Event) -> None:
        """Thread-safe event queue insertion."""
        try:
            self.event_queue.put_nowait(event)
        except asyncio.QueueFull:
            print(f"⚠️  Event queue full, dropping event: {event.type}")
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    async def run(self, user_message: str, message_id: str = "") -> asyncio.Queue[Event]:
        """
        Start agent execution with the given user message.
        
        Args:
            user_message: The user's input message
            message_id: Optional message ID for event correlation
        
        Returns:
            Queue that will receive events as the agent executes
        """
        self._message_id = message_id or f"msg_{id(self)}"
        
        # Add user message to conversation history
        self.messages.append({
            "role": "user",
            "content": [{"type": "text", "text": user_message}],
        })
        
        # Emit message start event
        start_event = create_event(
            EventType.STATUS,
            self._message_id,
            status="started",
            message="Processing your request...",
        )
        self._queue_event(start_event)
        
        # Start the agent loop in background
        self._task = asyncio.create_task(self._run_loop())
        
        return self.event_queue
    
    async def _run_loop(self) -> None:
        """
        Internal method that runs the sampling loop.
        
        Uses our forked tools with pre-built ToolCollection containing
        session-specific environment. No global os.environ modification!
        """
        try:
            # Map provider string to enum
            provider_map = {
                "anthropic": APIProvider.ANTHROPIC,
                "bedrock": APIProvider.BEDROCK,
                "vertex": APIProvider.VERTEX,
            }
            provider = provider_map.get(self.provider, APIProvider.ANTHROPIC)
            
            # Run the sampling loop with our pre-built tools
            # This is the key change: we pass tool_collection instead of
            # letting sampling_loop create tools with default environment
            self.messages = await sampling_loop(
                model=self.model,
                provider=provider,
                system_prompt_suffix=self.system_prompt_suffix,
                messages=self.messages,
                output_callback=self._output_callback,
                tool_output_callback=self._tool_output_callback,
                api_response_callback=self._api_response_callback,
                api_key=self.api_key,
                only_n_most_recent_images=3,
                max_tokens=self.max_tokens,
                tool_version=self.tool_version,
                thinking_budget=self.thinking_budget,
                tool_collection=self._tool_collection,  # Pre-built with session env!
            )
            
            # Emit completion event
            complete_event = message_complete_event(
                message_id=self._message_id,
                status="completed",
            )
            self._queue_event(complete_event)
            
        except Exception as e:
            # Emit error event
            err_event = error_event(
                error=str(e),
                code=type(e).__name__,
                message_id=self._message_id,
            )
            self._queue_event(err_event)
            
            # Still emit completion (with error status)
            complete_event = message_complete_event(
                message_id=self._message_id,
                status="error",
            )
            self._queue_event(complete_event)
    
    async def iter_events(self, timeout: float = 30.0):
        """
        Async iterator for consuming events.
        
        Yields events from the queue with keepalive on timeout.
        Stops when message_complete event is received.
        """
        while True:
            try:
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=timeout,
                )
                yield event
                
                if event.type == EventType.MESSAGE_COMPLETE:
                    break
                    
            except asyncio.TimeoutError:
                yield keepalive_event()
    
    async def cancel(self) -> None:
        """Cancel the running agent task."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    @property
    def is_running(self) -> bool:
        """Check if agent loop is currently executing."""
        return self._task is not None and not self._task.done()
