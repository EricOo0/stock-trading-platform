from google.adk.agents import Agent
from google.adk.agents import Agent
from backend.infrastructure.config.loader import config
from .tools import search_web, inspect_page
from .prompts import INSTRUCTION


from typing import Optional
from google.adk.agents import Agent
from backend.infrastructure.config.loader import config
from .tools import search_web, inspect_page
from .prompts import INSTRUCTION
from .callbacks import FrontendCallbackHandler

def create_deep_search_agent(event_queue=None) -> Agent:
    """
    Creates and configures the Deep Search Agent with optional callbacks.
    """
    # Load model dynamically
    model_name = config.get("model", "deepseek-ai/DeepSeek-V3.1-Terminus")
    if not model_name.startswith("openai/"):
         model_name = f"openai/{model_name}"

    callbacks = {}
    if event_queue:
        handler = FrontendCallbackHandler(event_queue)
        callbacks = {
            "before_tool_callback": handler.on_tool_start,
            "after_tool_callback": handler.on_tool_end,
            # "after_agent_callback": handler.on_agent_action # Uncomment if ADK supports this exact hook
        }

    return Agent(
        name="deep_search_agent",
        model=model_name,
        instruction=INSTRUCTION,
        tools=[search_web, inspect_page],
        description="Deep Search Agent for market sentiment research.",
        **callbacks
    )
