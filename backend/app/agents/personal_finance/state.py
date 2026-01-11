from typing import List, Dict, Any, Optional, TypedDict, Annotated
import operator
from langchain_core.messages import BaseMessage
from backend.app.agents.personal_finance.models import PortfolioSnapshot, RecommendationCard

class AgentState(TypedDict):
    # Chat History
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Input Context
    portfolio: Dict[str, Any] # Serialized PortfolioSnapshot
    user_id: str
    session_id: str
    memory_context: Optional[Dict[str, Any]] # Context from Memory System
    
    # Planning
    selected_agents: List[str] # ["macro", "market", "technical", "news"]
    
    # Execution Results
    macro_analysis: Optional[str]
    market_analysis: Optional[str]
    technical_analysis: Optional[str]
    news_analysis: Optional[str]
    daily_review_analysis: Optional[str]
    
    # Output
    final_report: str
    recommendation_cards: List[RecommendationCard]
