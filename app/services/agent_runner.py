"""
Agent Runner Service
====================

Wraps the Anthropic Computer Use sampling_loop with callbacks
that emit events to an async queue for SSE streaming.

This is the bridge between the Anthropic demo code and our FastAPI backend.
The key insight is that sampling_loop already accepts callbacks - we just
need to implement them to push events instead of updating Streamlit state.

Architecture:
    1. AgentRunner receives user message and session context
    2. Creates async queue and callback functions
    3. Spawns background task running sampling_loop
    4. Callbacks push Event objects to queue
    5. SSE endpoint consumes queue and streams to client
"""

import asyncio
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

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

# =============================================================================
# Import Anthropic Demo Code
# =============================================================================

# Add the computer_use_demo to Python path so we can import it
# This allows us to reuse the existing loop.py and tools unchanged
DEMO_PATH = Path(__file__).parent.parent.parent.parent / "computer-use-demo"
if str(DEMO_PATH) not in sys.path:
    sys.path.insert(0, str(DEMO_PATH))

try:
    from computer_use_demo.loop import APIProvider, sampling_loop
    from computer_use_demo.tools import ToolResult, ToolVersion
    ANTHROPIC_DEMO_AVAILABLE = True
except ImportError as e:
    # Allow running without the demo code (for testing schemas/routes)
    print(f"⚠️  Warning: Could not import computer_use_demo: {e}")
    print("   Agent functionality will be limited to mock responses.")
    ANTHROPIC_DEMO_AVAILABLE = False
    
    # Create mock types for type hints
    class APIProvider:  # type: ignore
        ANTHROPIC = "anthropic"
        BEDROCK = "bedrock"
        VERTEX = "vertex"
    
    class ToolResult:  # type: ignore
        output: str | None = None
        error: str | None = None
        base64_image: str | None = None
    
    ToolVersion = str


@dataclass
class AgentRunner:
    """
    Orchestrates agent execution with event streaming.
    
    Wraps the Anthropic sampling_loop with callbacks that push
    events to an async queue. The queue can be consumed by an
    SSE endpoint to stream real-time updates to the client.
    
    Attributes:
        session_id: Current session identifier
        model: Claude model to use
        provider: API provider (anthropic, bedrock, vertex)
        api_key: API key for the provider
        system_prompt_suffix: Custom instructions
        messages: Conversation history (mutable - updated by loop)
        display_env: DISPLAY environment for isolated X11 desktop
        event_queue: Queue for streaming events to SSE
        _task: Background task running the agent loop
    
    Example:
        runner = AgentRunner(
            session_id="sess_123",
            model="claude-sonnet-4-5-20250929",
            messages=[],
            display_env={"DISPLAY": ":1"},
        )
        queue = await runner.run("Search the weather in Santiago, Chile")
        
        # Consume events from queue
        async for event in runner.iter_events():
            yield event.to_sse()
    """
    
    session_id: str
    model: str
    provider: str = "anthropic"
    api_key: str = ""
    system_prompt_suffix: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    tool_version: str = "computer_use_20250124"  # Default for Claude 4.5
    max_tokens: int = 16384
    thinking_budget: int | None = None
    display_env: dict[str, str] | None = None  # DISPLAY env for isolated desktop
    
    # Internal state
    event_queue: asyncio.Queue[Event] = field(default_factory=asyncio.Queue)
    _task: asyncio.Task | None = field(default=None, repr=False)
    _message_id: str = field(default="", repr=False)
    
    def __post_init__(self):
        """Initialize API key from settings if not provided."""
        if not self.api_key:
            self.api_key = settings.anthropic_api_key.get_secret_value()
    
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
        
        Pushes appropriate event to the queue for SSE streaming.
        """
        block_type = content_block.get("type", "unknown")
        
        if block_type == "text":
            # Regular text response from Claude
            text_content = content_block.get("text", "")
            if text_content:
                event = text_event(text_content, self._message_id)
                self._queue_event(event)
                
        elif block_type == "thinking":
            # Extended thinking content
            thinking_content = content_block.get("thinking", "")
            if thinking_content:
                event = thinking_event(thinking_content, self._message_id)
                self._queue_event(event)
                
        elif block_type == "tool_use":
            # Claude wants to use a tool
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
        
        Emits tool result event with output, error, or screenshot.
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
        
        In production, this would log to a monitoring service.
        For now, we emit status events for debugging.
        """
        if error:
            # Emit error event
            err_event = error_event(
                error=str(error),
                code=type(error).__name__,
                message_id=self._message_id,
            )
            self._queue_event(err_event)
    
    def _queue_event(self, event: Event) -> None:
        """
        Thread-safe event queue insertion.
        
        Uses put_nowait since we're in sync callbacks but the
        queue is consumed by async code. The queue is unbounded
        so this won't block.
        """
        try:
            self.event_queue.put_nowait(event)
        except asyncio.QueueFull:
            # Shouldn't happen with unbounded queue, but handle gracefully
            print(f"⚠️  Event queue full, dropping event: {event.type}")
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    async def run(self, user_message: str, message_id: str = "") -> asyncio.Queue[Event]:
        """
        Start agent execution with the given user message.
        
        Adds the user message to conversation history and spawns
        a background task running the sampling loop.
        
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
        
        Handles the actual integration with Anthropic's code.
        Emits completion event when done (success or error).
        
        Note: Sets DISPLAY environment variable if display_env is provided.
        This is necessary for isolated X11 desktops per session.
        """
        import os
        
        # Set display environment for this session's isolated desktop
        original_display = os.environ.get("DISPLAY")
        if self.display_env and "DISPLAY" in self.display_env:
            os.environ["DISPLAY"] = self.display_env["DISPLAY"]
        
        try:
            if not ANTHROPIC_DEMO_AVAILABLE:
                # Mock response for testing without the demo
                await self._run_mock_loop()
                return
            
            # Map provider string to enum
            provider_map = {
                "anthropic": APIProvider.ANTHROPIC,
                "bedrock": APIProvider.BEDROCK,
                "vertex": APIProvider.VERTEX,
            }
            provider = provider_map.get(self.provider, APIProvider.ANTHROPIC)
            
            # Run the Anthropic sampling loop
            self.messages = await sampling_loop(
                model=self.model,
                provider=provider,
                system_prompt_suffix=self.system_prompt_suffix,
                messages=self.messages,
                output_callback=self._output_callback,
                tool_output_callback=self._tool_output_callback,
                api_response_callback=self._api_response_callback,
                api_key=self.api_key,
                only_n_most_recent_images=3,  # Keep context manageable
                max_tokens=self.max_tokens,
                tool_version=self.tool_version,
                thinking_budget=self.thinking_budget,
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
        
        finally:
            # Restore original DISPLAY environment
            if original_display is not None:
                os.environ["DISPLAY"] = original_display
            elif "DISPLAY" in os.environ and self.display_env:
                # We set it but there was no original, remove it
                del os.environ["DISPLAY"]
    
    async def _run_mock_loop(self) -> None:
        """
        Mock agent loop for testing without Anthropic demo.
        
        Simulates a simple response with tool usage.
        """
        # Simulate thinking
        await asyncio.sleep(0.5)
        self._output_callback({
            "type": "text",
            "text": "I'll help you with that. Let me search for the information...",
        })
        
        # Simulate tool use
        await asyncio.sleep(0.3)
        self._output_callback({
            "type": "tool_use",
            "id": "toolu_mock_123",
            "name": "computer",
            "input": {"action": "screenshot"},
        })
        
        # Simulate tool result  
        await asyncio.sleep(0.5)
        mock_result = type('MockResult', (), {
            'output': 'Screenshot captured successfully',
            'error': None,
            'base64_image': None,
        })()
        self._tool_output_callback(mock_result, "toolu_mock_123")
        
        # Final response
        await asyncio.sleep(0.3)
        self._output_callback({
            "type": "text",
            "text": "I've completed the task. This is a mock response since the Anthropic demo is not available.",
        })
        
        # Update messages with mock response
        self.messages.append({
            "role": "assistant",
            "content": [
                {"type": "text", "text": "I've completed the task. (Mock response)"},
            ],
        })
        
        # Completion
        complete_event = message_complete_event(
            message_id=self._message_id,
            status="completed",
        )
        self._queue_event(complete_event)
    
    async def iter_events(self, timeout: float = 30.0) -> asyncio.Queue[Event]:
        """
        Async iterator for consuming events.
        
        Yields events from the queue with keepalive on timeout.
        Stops when message_complete event is received.
        
        Args:
            timeout: Seconds to wait before emitting keepalive
        
        Yields:
            Event objects for SSE formatting
        """
        while True:
            try:
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=timeout,
                )
                yield event
                
                # Stop on completion
                if event.type == EventType.MESSAGE_COMPLETE:
                    break
                    
            except asyncio.TimeoutError:
                # Emit keepalive to maintain connection
                yield keepalive_event()
    
    async def cancel(self) -> None:
        """
        Cancel the running agent task.
        
        Useful for handling client disconnection or timeout.
        """
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

