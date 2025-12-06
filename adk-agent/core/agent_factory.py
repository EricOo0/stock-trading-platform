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
    Enforces the use of the custom LLM.
    """
    return Agent(
        model=get_model(),
        name=name,
        instruction=instruction,
        tools=tools or [],
        description=description or name
    )
