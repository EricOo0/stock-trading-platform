import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional
from .schemas import EventType, TaskUpdateType, TaskUpdatePayload

logger = logging.getLogger(__name__)

class TaskCallbackHandler:
    """
    Callback handler that emits events bound to a specific task_id.
    """
    def __init__(self, event_queue: asyncio.Queue, task_id: str):
        self.event_queue = event_queue
        self.task_id = task_id
        self.last_response_text = ""

    async def _emit(self, update_type: TaskUpdateType, content: str, **kwargs):
        try:
            logger.info(f"[Callback] Emitting {update_type} for task {self.task_id} (content len={len(content)})")
            payload = TaskUpdatePayload(
                task_id=self.task_id,
                type=update_type,
                content=content,
                timestamp=int(time.time() * 1000),
                **kwargs
            )
            
            event = {
                "type": EventType.TASK_UPDATE,
                "payload": payload.model_dump()
            }
            
            await self.event_queue.put(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Error emitting callback event: {e}")

    async def on_model_start(self, *args, **kwargs):
        """Called before the LLM is invoked. Use as 'Thinking' state."""
        # Extract user message if possible
        request = kwargs.get('llm_request')
        if not request and len(args) >= 2:
            request = args[1]
            
        content = "Thinking..."
        # Try to get more detail if needed, but "Thinking..." is usually enough for UI state
        
        await self._emit(TaskUpdateType.THOUGHT, content)

    async def on_model_end(self, *args, **kwargs):
        """Called after LLM generates a response."""
        response = kwargs.get('llm_response')
        if not response and len(args) >= 2:
            response = args[1]

        content = ""
        if response and hasattr(response, 'content'):
            if hasattr(response.content, 'parts') and response.content.parts:
                for part in response.content.parts:
                    if hasattr(part, 'text') and part.text:
                        content += part.text
        
        # We handle tool calls separately via on_tool_start
        # If content is empty (pure tool call), we might skip or show "Calling tool..."
        if content:
            self.last_response_text = content
            await self._emit(TaskUpdateType.THOUGHT, content) # Treat model output as thought/text

    async def on_tool_start(self, *args, **kwargs):
        """Called when a tool starts execution."""
        tool_obj = kwargs.get('tool')
        tool_args = kwargs.get('args')
        
        if not tool_args and len(args) >= 2:
             tool_args = args[1]

        tool_name = getattr(tool_obj, 'name', 'unknown_tool') if tool_obj else 'unknown_tool'
        
        await self._emit(
            TaskUpdateType.TOOL_CALL, 
            f"Calling {tool_name}...", 
            tool_name=tool_name, 
            tool_input=str(tool_args)
        )

    async def on_tool_end(self, *args, **kwargs):
        """Called when a tool finishes execution."""
        tool_obj = kwargs.get('tool')
        result = kwargs.get('tool_response')
        
        if result is None and len(args) >= 4:
             result = args[3]
        
        tool_name = getattr(tool_obj, 'name', 'unknown_tool') if tool_obj else 'unknown_tool'
        
        # Truncate result for display
        output_str = str(result)
        display_output = output_str[:500] + "..." if len(output_str) > 500 else output_str
        
        await self._emit(
            TaskUpdateType.TOOL_RESULT,
            f"Tool {tool_name} finished.",
            tool_name=tool_name,
            tool_output=display_output
        )

    async def on_agent_end(self, *args, **kwargs):
        pass
