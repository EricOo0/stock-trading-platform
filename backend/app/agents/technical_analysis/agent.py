from google.adk.agents import Agent
from backend.infrastructure.config.loader import config
from .prompts import TECHNICAL_ANALYSIS_INSTRUCTION
from typing import Optional
from .callbacks import TechnicalAnalysisCallbackHandler
from .tools import get_stock_price, get_historical_data, get_technical_indicators

def create_technical_analysis_agent(handler: Optional[TechnicalAnalysisCallbackHandler] = None) -> Agent:
    """
    Creates and configures the Technical Analysis Agent.
    """
    # Load model
    model_name = config.get("model", "deepseek-ai/DeepSeek-V3.1-Terminus")
    if not model_name.startswith("openai/"):
         model_name = f"openai/{model_name}"

    callbacks = {}
    if handler:
        callbacks = {
            "before_model_callback": handler.on_model_start,
            "after_model_callback": handler.on_model_end, 
        }

    return Agent(
        name="technical_analysis_agent",
        model=model_name,
        instruction=TECHNICAL_ANALYSIS_INSTRUCTION,
        tools=[get_stock_price, get_historical_data, get_technical_indicators],
        description="Analyzes stock technical indicators and price action to provide trading signals.",
        **callbacks
    )
