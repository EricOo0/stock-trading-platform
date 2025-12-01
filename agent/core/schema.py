from pydantic import BaseModel, Field
from typing import Literal

class CallAgent(BaseModel):
    """Call a specialist agent to gather information."""
    agent: Literal["MacroDataInvestigator", "MarketDataInvestigator", "SentimentInvestigator", "WebSearchInvestigator"] = Field(..., description="The specialist agent to call")
    instruction: str = Field(..., description="Specific task/question for the agent")

class ResearchBrief(BaseModel):
    """Structured output for the Receptionist's research brief."""
    brief: str = Field(..., description="A concise, actionable research brief starting with 'RESEARCH BRIEF:'")
