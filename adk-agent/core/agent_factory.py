from .memory_agent import MemoryAwareAgent
from google.adk.agents import Agent
from core.llm import get_model
from typing import List, Optional

def create_agent(
    name: str,
    instruction: str,
    tools: Optional[List] = None,
    description: Optional[str] = None
) -> Agent:
    """
    Factory to create an ADK Agent with standard configuration.
    Enforces the use of the custom LLM and Memory System.
    """
    # Derive a simple agent_id from the name (e.g., "Chairman" -> "chairman_agent")
    agent_id = f"{name.lower()}_agent"
    
    return MemoryAwareAgent(
        agent_id=agent_id,
        model=get_model(), # Using the custom LLM
        name=name,
        instruction=instruction,
        tools=tools or [],
        description=description or name
    )
