import asyncio
import json
import time
from typing import Dict, Any, Optional

class FrontendCallbackHandler:
    def __init__(self, event_queue: asyncio.Queue):
        self.event_queue = event_queue

    async def on_tool_start(self, *args, **kwargs):
        """Called when a tool starts execution."""
        # ADK standard arguments extraction
        tool_obj = kwargs.get('tool')
        tool_args = kwargs.get('args')
        
        # Fallback for positional args if needed (though kwargs is standard)
        if not tool_obj and len(args) > 0:
             # Just a best guess if positional
             pass

        tool_name = getattr(tool_obj, 'name', 'unknown_tool') if tool_obj else 'unknown_tool'
        tool_input = str(tool_args) if tool_args is not None else ""

        event = {
            "type": "tool",
            "status": "start",
            "tool": tool_name,
            "input": tool_input,
            "timestamp": int(time.time() * 1000)
        }
        await self.event_queue.put(json.dumps(event) + "\n")

    async def on_tool_end(self, *args, **kwargs):
        """Called when a tool finishes execution."""
        tool_obj = kwargs.get('tool')
        tool_response = kwargs.get('tool_response')
        
        tool_name = getattr(tool_obj, 'name', 'unknown_tool') if tool_obj else 'unknown_tool'
        
        event = {
            "type": "tool",
            "status": "end",
            "tool": tool_name,
            "output": str(tool_response),
            "timestamp": int(time.time() * 1000)
        }
        await self.event_queue.put(json.dumps(event) + "\n")

    async def on_agent_action(self, action: Any, **kwargs):
        """Called when agent decides to take an action (thought)."""
        # If action has log or thought, emit it.
        # This depends on the ADK AgentAction structure.
        pass
