from pydantic import BaseModel, Field
from typing import Literal, List, Optional

class Step(BaseModel):
    agent: Literal["MacroDataInvestigator", "MarketDataInvestigator", "SentimentInvestigator", "WebSearchInvestigator"] = Field(..., description="The agent to perform this step")
    instruction: str = Field(..., description="Specific instruction for the agent")

class CreatePlan(BaseModel):
    """Create a step-by-step investigation plan."""
    steps: List[Step] = Field(..., description="List of steps to execute sequentially")

class ResearchBrief(BaseModel):
    """Structured output for the Receptionist's research brief."""
    brief: str = Field(..., description="A concise, actionable research brief starting with 'RESEARCH BRIEF:'")
