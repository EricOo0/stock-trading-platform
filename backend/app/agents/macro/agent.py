from typing import Optional
from google.adk.agents import Agent
from backend.infrastructure.config.loader import config
from .prompts import MACRO_ANALYSIS_INSTRUCTION
from .callbacks import MacroCallbackHandler
from .tools import get_macro_data, get_macro_history

def create_macro_agent(callback_handler: Optional[MacroCallbackHandler] = None) -> Agent:
    """
    Creates the Macro Analysis Agent, configured via standardized config.
    """
    
    # Load model from config (aligned with other agents)
    model_name = config.get("model", "deepseek-ai/DeepSeek-V3.1-Terminus")
    if not model_name.startswith("openai/"):
         model_name = f"openai/{model_name}"

    callbacks = {}
    
    if callback_handler:
        callbacks = {
            "before_model_callback": callback_handler.on_model_start,
            "after_model_callback": callback_handler.on_model_end, 
        }

    agent = Agent(
        name="macro_analysis_agent",
        model=model_name,
        instruction=MACRO_ANALYSIS_INSTRUCTION,
        tools=[get_macro_data, get_macro_history],
        description="Analyzes global macro-economic indicators to provide market cycle judgment.",
        **callbacks
    )

    return agent
