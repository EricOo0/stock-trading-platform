from google.adk.agents import Agent
from typing import List, Optional
from .llm import get_model

def create_agent(
    name: str,
    instruction: str,
    tools: Optional[List] = None,
    description: Optional[str] = None,
    enable_memory: bool = True
) -> Agent:
    """
    Factory to create an ADK Agent with standard configuration.
    
    Args:
        name: Agent name
        instruction: Agent instruction/prompt
        tools: List of tools available to the agent
        description: Agent description
        enable_memory: Whether to enable memory tools (default: True)
    
    Returns:
        Configured Agent instance with memory capabilities
    """
    agent_tools = tools or []
    
    # Add memory tools if enabled
    if enable_memory:
        from .memory_tools import create_memory_tools_for_agent
        # Derive agent_id from name
        agent_id = f"{name.lower().replace(' ', '')}_agent"
        memory_tool_list = create_memory_tools_for_agent(agent_id)
        agent_tools.extend(memory_tool_list)
        
        # Enhance instruction to guide memory usage
        memory_guidance = """

🧠 **记忆系统使用指南**：
- 当用户提到"记住"、"我的偏好"、"上次"等词时，使用 `search_memory` 工具查询相关信息
- 当用户明确表达重要原则或偏好时，使用 `save_important_fact` 工具保存
- 在做出重要决策前，可以主动搜索记忆以参考历史经验
"""
        instruction = instruction + memory_guidance
    
    return Agent(
        model=get_model(),
        name=name,
        instruction=instruction,
        tools=agent_tools,
        description=description or name
    )
