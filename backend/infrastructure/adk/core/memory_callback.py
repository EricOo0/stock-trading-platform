"""
ADK Callback Handler for Automatic Memory Saving

This module implements callback handlers that automatically save agent interactions
to the Memory System at key execution points:
- before_model: Save user query
- after_model: Save agent response
- before_tool: Save tool call inputs
- after_tool: Save tool call outputs
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime
from .memory_client import MemoryClient

logger = logging.getLogger(__name__)


class MemoryCallbackHandler:
    """
    Handles ADK callbacks to automatically save memories.
    
    Each Agent instance should have its own handler with a unique agent_id.
    """
    
    def __init__(self, agent_id: str, memory_base_url: str = "http://localhost:10000"):
        """
        Initialize the callback handler.
        
        Args:
            agent_id: Unique identifier for the agent (e.g., "chairman_agent")
            memory_base_url: Base URL of the Memory System API
        """
        self.agent_id = agent_id
        self.memory_client = MemoryClient(
            base_url=memory_base_url,
            agent_id=agent_id
        )
        logger.info(f"MemoryCallbackHandler initialized for {agent_id}")
    
    def before_model(self, *args, **kwargs) -> None:
        """
        Called before LLM is invoked. Saves user query to memory.
        """
        try:
            # ADK passes keyword arguments: callback_context, llm_request
            request = kwargs.get('llm_request')
            if not request and len(args) >= 2:
                 request = args[1]
            print("--- 完整的 LLM 请求 (LlmRequest) ---")
            # 打印完整的请求对象，它包含了所有组成 Prompt 的部分
            print(request) 
            print("---------------------------------")
            if request:
                # Extract user message from request
                user_msg = ""
                if hasattr(request, 'contents'):
                    for content in request.contents:
                        if hasattr(content, 'parts'):
                            for part in content.parts:
                                if hasattr(part, 'text') and part.text:
                                    user_msg = part.text
                
                if user_msg:
                    self.memory_client.add_memory(
                        content=user_msg,
                        role="user",
                        metadata={
                            "timestamp": datetime.now().isoformat(),
                            "source": "before_model_callback",
                            "agent_name": self.agent_id
                        }
                    )
        except Exception as e:
            print(f"[{self.agent_id}] before_model failed: {e}", flush=True)

    def after_model(self, *args, **kwargs) -> None:
        """
        Called after LLM generates response.
        """
        try:
            # ADK passes keyword arguments: callback_context, llm_response
            response = kwargs.get('llm_response')
            if not response and len(args) >= 2:
                response = args[1]

            if response:
                response_text = ""
                if hasattr(response, 'contents'):
                     for content in response.contents:
                        if hasattr(content, 'parts'):
                            for part in content.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_text += part.text
                
                if response_text:
                    self.memory_client.add_memory(
                        content=response_text,
                        role="agent",
                        metadata={
                            "timestamp": datetime.now().isoformat(),
                            "source": "after_model_callback",
                            "agent_name": self.agent_id
                        }
                    )
        except Exception as e:
            print(f"[{self.agent_id}] after_model failed: {e}", flush=True)

    def before_tool(self, *args, **kwargs) -> None:
        """Called before tool execution."""
        try:
            # ADK likely passes: tool, args, tool_context
            tool_data = kwargs.get('args') # This is the tools arguments dict
            tool_obj = kwargs.get('tool')
            
            if not tool_data and len(args) >= 2:
                tool_data = args[1]
            
            if tool_data or tool_obj:
                # Try to extract tool info
                tool_name = getattr(tool_obj, 'name', 'unknown') if tool_obj else 'unknown'
                
                self.memory_client.add_memory(
                    content=f"Calling tool: {tool_name} with {tool_data}",
                    role="system",
                    metadata={
                        "timestamp": datetime.now().isoformat(),
                        "source": "before_tool_callback",
                        "tool_name": tool_name,
                        "agent_name": self.agent_id
                    }
                )
        except Exception as e:
            print(f"[{self.agent_id}] before_tool failed: {e}", flush=True)

    def after_tool(self, *args, **kwargs) -> None:
        """Called after tool execution."""
        try:
            # ADK passes: tool, args, tool_context, tool_response
            result = kwargs.get('tool_response')
            if not result and len(args) >= 2:
                # warning: signature might be different
                result = args[-1] 
                
            self.memory_client.add_memory(
                content=f"Tool result: {str(result)[:200]}...",
                role="system",
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "source": "after_tool_callback",
                    "agent_name": self.agent_id
                }
            )
        except Exception as e:
             print(f"[{self.agent_id}] after_tool failed: {e}", flush=True)
