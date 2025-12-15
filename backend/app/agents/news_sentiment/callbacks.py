import asyncio
import json
import time
from typing import Dict, Any, Optional
from google.adk.models import LlmResponse, LlmRequest

class FrontendCallbackHandler:
    def __init__(self, event_queue: asyncio.Queue):
        self.event_queue = event_queue

    async def on_model_start(self, *args, **kwargs):
        """Called before the LLM is invoked. Use as 'Thinking' state."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[Callback Debug] on_model_start args: {args}")
        print(f"[Callback Debug] on_model_start args: {args}")
        logger.info(f"[Callback Debug] on_model_start kwargs: {kwargs.keys()}")
        print(f"[Callback Debug] on_model_start kwargs: {kwargs.keys()}")
        if 'llm_request' in kwargs:
             logger.info(f"[Callback Debug] llm_request type: {type(kwargs['llm_request'])}")
             logger.info(f"[Callback Debug] llm_request vars: {vars(kwargs['llm_request']) if hasattr(kwargs['llm_request'], '__dict__') else 'no dict'}")
             print(f"[Callback Debug] llm_request type: {type(kwargs['llm_request'])}")
             print(f"[Callback Debug] llm_request vars: {vars(kwargs['llm_request']) if hasattr(kwargs['llm_request'], '__dict__') else 'no dict'}")

        # ADK passes: callback_context, llm_request
        request = kwargs.get('llm_request')
        if not request and len(args) >= 2:
            request = args[1] # fallback
        
        user_msg = ""
        # Official Reference: request.contents[-1].parts[0].text
        if request and hasattr(request, 'contents') and request.contents:
            last_msg = request.contents[-1]
            if hasattr(last_msg, 'role') and last_msg.role == 'user':
                if hasattr(last_msg, 'parts') and last_msg.parts:
                    # Check first part for text
                    if hasattr(last_msg.parts[0], 'text'):
                        user_msg = last_msg.parts[0].text
        
        # Emit a THOUGHT event so frontend renders it
        # If user_msg is found, show it. Otherwise generic message.
        content = f"Thinking Process: Analyzing request '{user_msg}'..." if user_msg else "Thinking Process: Analyzing..."
        
        event = {
            "type": "thought",
            "content": content + "\n",
            "timestamp": int(time.time() * 1000)
        }
        await self.event_queue.put(json.dumps(event) + "\n")

    async def on_model_end(self, *args, **kwargs):
        """Called after LLM generates a response."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[Callback Debug] on_model_end args: {args}")
        logger.info(f"[Callback Debug] on_model_end kwargs: {kwargs.keys()}")
        print(f"[Callback Debug] on_model_end kwargs: {kwargs.keys()}")
        print(f"[Callback Debug] on_model_end args: {args}")
        # ADK passes: callback_context, llm_response
        response = kwargs.get('llm_response')
        logger.info(f"[Callback Debug] llm_response: {response}")
        if not response and len(args) >= 2:
            response = args[1] # fallback

        content = ""
        # Official Reference: response.content.parts[0].text
        if response and hasattr(response, 'content'):
            if hasattr(response.content, 'parts') and response.content.parts:
                for part in response.content.parts:
                    # Capture Text
                    if hasattr(part, 'text') and part.text:
                        content += part.text
                    # Ignore function_call (handled by tool callbacks)
                    
        # Check for error message
        if response and hasattr(response, 'error_message') and response.error_message:
             content = f"Error: {response.error_message}"

        if content:
            event = {
                "type": "thought",
                "content": content,
                "timestamp": int(time.time() * 1000)
            }
            await self.event_queue.put(json.dumps(event) + "\n")

    async def on_tool_start(self, *args, **kwargs):
        """Called when a tool starts execution."""
        # ADK likely passes: tool, args, tool_context
        tool_obj = kwargs.get('tool')
        tool_args = kwargs.get('args')
        
        if not tool_args and len(args) >= 2:
             tool_args = args[1]

        tool_name = getattr(tool_obj, 'name', 'unknown_tool') if tool_obj else 'unknown_tool'
        
        event = {
            "type": "tool",
            "status": "start",
            "tool": tool_name.upper(),
            "input": str(tool_args),
            "timestamp": int(time.time() * 1000)
        }
        await self.event_queue.put(json.dumps(event) + "\n")

    async def on_tool_end(self, *args, **kwargs):
        """Called when a tool finishes execution."""
        # ADK passes: tool, args, tool_context, tool_response
        tool_obj = kwargs.get('tool')
        result = kwargs.get('tool_response')
        
        if result is None and len(args) >= 4:
             result = args[3] # dangerous guess, fallback
        
        tool_name = getattr(tool_obj, 'name', 'unknown_tool') if tool_obj else 'unknown_tool'
        
        event = {
            "type": "tool",
            "status": "end",
            "tool": tool_name.upper(),
            "output": str(result)[:500] + "..." if len(str(result)) > 500 else str(result),
            "timestamp": int(time.time() * 1000)
        }
        await self.event_queue.put(json.dumps(event) + "\n")

    async def on_agent_end(self, *args, **kwargs):
        pass
