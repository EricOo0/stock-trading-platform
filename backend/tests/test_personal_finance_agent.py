import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.agents.personal_finance.agent import create_personal_finance_graph, planner_node, executor_node, synthesizer_node
from backend.app.agents.personal_finance.models import PortfolioSnapshot, AssetItem, RecommendationCard
from langchain_core.messages import HumanMessage, AIMessage

# Mock State
@pytest.fixture
def mock_state():
    return {
        "messages": [HumanMessage(content="Review my portfolio")],
        "portfolio": {
            "assets": [
                {"symbol": "AAPL", "type": "Stock", "quantity": 10}
            ]
        },
        "user_id": "test_user",
        "session_id": "test_session",
        "selected_agents": []
    }

@pytest.mark.asyncio
async def test_planner_node(mock_state):
    # Mock LLM response
    mock_llm_response = AIMessage(content='{"agents": ["macro", "news"]}')
    
    with patch("backend.app.agents.personal_finance.agent.get_llm") as mock_get_llm:
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value = mock_llm_response
        mock_get_llm.return_value = mock_llm_instance
        
        result = await planner_node(mock_state)
        
        assert "selected_agents" in result
        assert "macro" in result["selected_agents"]
        assert "news" in result["selected_agents"]
        assert "technical" not in result["selected_agents"]

@pytest.mark.asyncio
async def test_executor_node(mock_state):
    mock_state["selected_agents"] = ["macro", "technical"]
    
    with patch("backend.app.agents.personal_finance.agent.run_macro_analysis", new_callable=AsyncMock) as mock_macro, \
         patch("backend.app.agents.personal_finance.agent.run_technical_analysis", new_callable=AsyncMock) as mock_tech:
        
        mock_macro.return_value = "Macro looks good."
        mock_tech.return_value = "Technical indicates buy."
        
        result = await executor_node(mock_state)
        
        assert result["macro_analysis"] == "Macro looks good."
        assert "Technical indicates buy" in result["technical_analysis"]
        assert mock_macro.called
        assert mock_tech.called

@pytest.mark.asyncio
async def test_synthesizer_node(mock_state):
    mock_state["macro_analysis"] = "Macro OK"
    mock_state["market_analysis"] = "Market Bullish"
    
    # Mock LLM responses (Card generation + Report generation)
    # The node calls LLM twice.
    
    mock_card_json = """
    {
        "cards": [
            {
                "title": "Buy Tech",
                "description": "Sector is strong",
                "action": "buy",
                "confidence_score": 0.9,
                "risk_level": "medium"
            }
        ]
    }
    """
    mock_report_content = "## Final Report\n\nEverything is awesome."
    
    with patch("backend.app.agents.personal_finance.agent.get_llm") as mock_get_llm:
        mock_llm_instance = AsyncMock()
        # Side effect for consecutive calls
        mock_llm_instance.ainvoke.side_effect = [
            AIMessage(content=mock_card_json),
            AIMessage(content=mock_report_content)
        ]
        mock_get_llm.return_value = mock_llm_instance
        
        result = await synthesizer_node(mock_state)
        
        assert "final_report" in result
        assert "recommendation_cards" in result
        assert result["final_report"] == mock_report_content
        assert len(result["recommendation_cards"]) == 1
        assert result["recommendation_cards"][0].title == "Buy Tech"
