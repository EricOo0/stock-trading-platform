import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.agents.personal_finance.sub_agents import (
    MacroAnalyst,
    MarketAnalyst,
    NewsAnalyst,
    TechnicalAnalyst
)

@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.ainvoke.return_value = MagicMock(content="Analysis Result")
    return llm

@pytest.fixture
def mock_registry():
    registry = MagicMock()
    # Mock methods to return simple data or futures
    # Since sub_agents use asyncio.to_thread, we need to mock the synchronous methods of registry
    registry.get_macro_data.return_value = {"value": 100}
    registry.search_market_news.return_value = [{"title": "News 1"}]
    registry.get_historical_data.return_value = [{"close": 10}]
    return registry

@pytest.mark.asyncio
async def test_macro_analyst(mock_llm, mock_registry):
    with patch("backend.app.agents.personal_finance.sub_agents.registry", mock_registry), \
         patch("backend.app.agents.personal_finance.sub_agents.ChatOpenAI", return_value=mock_llm):
        
        analyst = MacroAnalyst()
        result = await analyst.analyze()
        
        assert result == "Analysis Result"
        # Verify registry calls (synchronous)
        assert mock_registry.get_macro_data.call_count > 0
        # Verify LLM call
        mock_llm.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_news_analyst(mock_llm, mock_registry):
    with patch("backend.app.agents.personal_finance.sub_agents.registry", mock_registry), \
         patch("backend.app.agents.personal_finance.sub_agents.ChatOpenAI", return_value=mock_llm):
        
        analyst = NewsAnalyst()
        result = await analyst.analyze("AAPL")
        
        assert result == "Analysis Result"
        mock_registry.search_market_news.assert_called_with(query="AAPL", limit=5)
        mock_llm.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_technical_analyst(mock_llm, mock_registry):
    with patch("backend.app.agents.personal_finance.sub_agents.registry", mock_registry), \
         patch("backend.app.agents.personal_finance.sub_agents.ChatOpenAI", return_value=mock_llm):
        
        analyst = TechnicalAnalyst()
        result = await analyst.analyze("AAPL")
        
        assert result == "Analysis Result"
        mock_registry.get_historical_data.assert_called_with(symbol="AAPL", period="30d")
        mock_llm.ainvoke.assert_called_once()
