from google.adk.agents import LlmAgent
from typing import List, Optional
from .llm import get_model
from .memory_callback import MemoryCallbackHandler

def create_agent(
    name: str,
    instruction: str,
    tools: Optional[List] = None,
    description: Optional[str] = None,
    enable_memory: bool = True
) -> LlmAgent:
    """
    Factory to create an ADK LlmAgent with standard configuration.
    
    Args:
        name: Agent name
        instruction: Agent instruction/prompt
        tools: List of tools available to the agent
        description: Agent description
        enable_memory: Whether to enable memory integration (default: True)
    
    Returns:
        Configured LlmAgent instance with automatic memory capturing via callbacks
    """
    print(f"DEBUG: create_agent called for {name}, enable_memory={enable_memory}", flush=True)
    agent_tools = tools or []
    
    # Derive agent_id from name (normalize to snake_case)
    agent_id = f"{name.lower().replace(' ', '')}_agent"
    
    # Create callback handler for automatic memory saving
    callback_handler = None
    if enable_memory:
        callback_handler = MemoryCallbackHandler(
            agent_id=agent_id,
            memory_base_url="http://localhost:10000"
        )
        
        # Add memory search tool (read capability)
        from .memory_tools import create_memory_tools_for_agent
        memory_tool_list = create_memory_tools_for_agent(agent_id)
        agent_tools.extend(memory_tool_list)
        
        # Enhance instruction to guide memory usage
        memory_guidance = """

🧠 **记忆系统**：
- 系统会自动记录所有对话和工具调用
- 使用 `search_memory` 工具查询历史信息（如用户偏好、过往分析等）
- 主动检索记忆可以提供更个性化和上下文相关的服务
"""
        instruction = instruction + memory_guidance
    
    # Create agent with callback handlers
    agent_kwargs = {
        "model": get_model(),
        "name": name,
        "instruction": instruction,
        "tools": agent_tools,
        "description": description or name,
    }
    
    # Register callbacks if memory is enabled
    if callback_handler:
        agent_kwargs.update({
            "before_model_callback": callback_handler.before_model,
            "after_model_callback": callback_handler.after_model,
            "before_tool_callback": callback_handler.before_tool,
            "after_tool_callback": callback_handler.after_tool,
        })
    
    agent = LlmAgent(**agent_kwargs)
    
    return agent
