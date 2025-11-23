import operator
from typing import Annotated, List, Sequence, TypedDict, Union, Dict, Any
from pydantic import BaseModel, Field

from langchain_core.messages import BaseMessage

class Evidence(BaseModel):
    """Structured evidence gathered by specialists."""
    source: str = Field(..., description="The agent or tool that provided the evidence")
    content: str = Field(..., description="The actual data or finding")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")

class AgentState(TypedDict):
    """
    The state of the agent graph (Boardroom Pattern).
    """
    # Conversation history (Standard LangGraph)
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Structured State
    research_brief: str # The clarified intent/task from Receptionist
    evidence_log: Annotated[List[Dict[str, Any]], operator.add] # Log of Evidence objects (as dicts for serialization)
    review_count: int # Counter to prevent infinite loops
    
    # Routing
    next: str # The next node to execute
    plan: List[Dict[str, str]] # List of planned steps (Overwritten each step)
