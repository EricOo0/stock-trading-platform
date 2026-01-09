from backend.app.agents.research.models import DeepResearchReport
from langchain_core.tools import tool
import asyncio
import logging
import json
from typing import Optional, List, Dict, Any
from backend.app.registry import Tools
from backend.infrastructure.config.loader import config

logger = logging.getLogger(__name__)

# Initialize the centralized tools registry
# This handles all API keys and sub-tool initialization automatically via config
registry_tools = Tools()


@tool
async def search_google(query: str) -> str:
    """
    Search Google (or other providers like Tavily/SerpApi) for real-time market news and information.
    Use this to find current events, news, or general information not covered by specific data tools.
    """
    try:
        # Use registry's search_market_news which handles provider fallback (Tavily -> Serp -> DDG)
        # Run in thread pool to avoid blocking async loop
        results = await asyncio.to_thread(
            registry_tools.search_market_news,
            query=query,
            provider="auto",
            topic="news",
        )

        if not results:
            return "No search results found."

        return json.dumps(results, default=str)
    except Exception as e:
        logger.error(f"Search tool error: {e}")
        return f"Error performing search: {str(e)}"


@tool
async def get_market_data(symbol: str, period: str = "1y") -> str:
    """
    Get historical stock market data (OHLCV).
    Args:
        symbol: Stock symbol (e.g., 'AAPL', '00700.HK', '600519').
        period: Time period. Valid values: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'.
    """
    try:
        # Run in thread pool
        data = await asyncio.to_thread(
            registry_tools.get_historical_data, symbol=symbol, period=period
        )

        if not data:
            return f"No market data found for {symbol}."

        # If it's a list, it's likely the OHLCV data
        if isinstance(data, list):
            # Limit to recent 30 records to save tokens, unless it's short
            summary_data = data[-30:] if len(data) > 30 else data
            return json.dumps(summary_data, default=str)

        return str(data)
    except Exception as e:
        logger.error(f"Get market data error: {e}")
        return f"Error getting market data: {str(e)}"


@tool
async def get_macro_economic_data(query: str) -> str:
    """
    Get macro economic indicators (e.g. GDP, CPI, Unemployment, Interest Rate).
    Args:
        query: Description of the data needed (e.g., 'US CPI', 'China GDP', 'Fed Interest Rate').
    """
    try:
        # Try history first as it's more useful for research
        data = await asyncio.to_thread(
            registry_tools.get_macro_history, query=query, period="1y"
        )

        if isinstance(data, dict) and "error" in data:
            # Fallback to snapshot data if history fails or specific query structure
            data = await asyncio.to_thread(registry_tools.get_macro_data, query=query)

        return json.dumps(data, default=str)
    except Exception as e:
        logger.error(f"Get macro data error: {e}")
        return f"Error getting macro data: {str(e)}"


@tool
async def get_technical_indicators(symbol: str, period: str = "60d") -> str:
    """
    Get summarized technical analysis indicators (MA, MACD, RSI, etc.).
    Args:
        symbol: Stock symbol.
        period: Data period to calculate on (default '60d').
    """
    try:
        indicators = await asyncio.to_thread(
            registry_tools.get_technical_indicators, symbol=symbol, period=period
        )
        return json.dumps(indicators, default=str)
    except Exception as e:
        return f"Error calculating technical indicators: {str(e)}"


@tool
async def get_financial_metrics(symbol: str) -> str:
    """
    Get key financial metrics for a company (Revenue, Net Income, etc.).
    Args:
        symbol: Stock symbol.
    """
    try:
        metrics = await asyncio.to_thread(
            registry_tools.get_financial_metrics, symbol=symbol
        )
        return json.dumps(metrics, default=str)
    except Exception as e:
        return f"Error getting financial metrics: {str(e)}"


@tool
async def get_company_report(symbol: str) -> str:
    """
    Get latest financial report metadata and download link.
    Args:
        symbol: Stock symbol.
    """
    try:
        report = await asyncio.to_thread(
            registry_tools.get_company_report, symbol=symbol
        )
        return json.dumps(report, default=str)
    except Exception as e:
        return f"Error getting company report: {str(e)}"


@tool
async def get_discussion_wordcloud(query: str) -> str:
    """
    Get word cloud data and sentiment summary from social media (Xueqiu) for a stock or topic.
    Returns keywords, weights, and sentiment labels, plus a summary for LLM analysis.
    """
    try:
        # Run in thread pool
        data = await asyncio.to_thread(
            registry_tools.get_discussion_wordcloud, query=query
        )
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Word cloud tool error: {e}")
        return f"Error getting word cloud data: {str(e)}"


@tool
async def get_sector_fund_flow(limit: int = 10, sort_by: str = "hot", sector_type: str = "industry") -> str:
    """
    Get A-share sector fund flow ranking to identify hot or cold sectors.
    Args:
        limit: Number of sectors to return (default 10).
        sort_by: 'hot' (highest net inflow) or 'cold' (highest net outflow).
        sector_type: 'industry' (default) or 'concept'. Use 'concept' to find hot themes/topics.
    """
    from backend.app.services.market_service import market_service
    try:
        if sort_by == "cold":
            data = await asyncio.to_thread(market_service.get_cold_sectors, limit, sector_type)
        else:
            data = await asyncio.to_thread(market_service.get_hot_sectors, limit, sector_type)
            
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return f"Error getting sector fund flow: {str(e)}"


@tool
async def get_sector_top_stocks(sector_name: str, limit: int = 5, sector_type: str = "industry") -> str:
    """
    Get top component stocks (leaders) of a specific A-share sector.
    Args:
        sector_name: Exact name of the sector (e.g. '软件开发', 'Sora概念').
        limit: Number of stocks to return (default 5).
        sector_type: 'industry' (default) or 'concept'. Must match the type of sector_name.
    """
    from backend.app.services.market_service import market_service
    try:
        data = await asyncio.to_thread(market_service.get_sector_details, sector_name, sort_by="amount", limit=limit, sector_type=sector_type)
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return f"Error getting sector stocks: {str(e)}"


# Export tools list
tools = [
    search_google,
    get_market_data,
    get_macro_economic_data,
    get_technical_indicators,
    get_financial_metrics,
    get_company_report,
    get_discussion_wordcloud,
    get_sector_fund_flow,
    get_sector_top_stocks,
]


@tool
async def submit_research_report(
    signals: List[Dict[str, str]],
    analysis: str,
    outlook: Dict[str, Any],
    references: List[Dict[str, str]]
) -> str:
    """
    Submit the FINAL Deep Research Report. You MUST call this tool when you have completed your analysis.

    Args:
        signals: List of key signals, e.g. [{"condition": "High Volume", "result": "Buy"}].
        analysis: The main text summary of your trend analysis (1-2 paragraphs).
        outlook: The market outlook, e.g. {"score": 80, "label": "Optimism"}. Score 0-100.
        references: List of sources, e.g. [{"id": "1", "title": "News Title", "source": "Bloomberg", "url": "..."}].
    """
    try:
        # Validate using Pydantic model
        report = DeepResearchReport(
            signals=signals,
            analysis=analysis,
            outlook=outlook,
            references=references
        )
        # Return the JSON string. The callback will catch this specific tool and parse it.
        return report.json()
    except Exception as e:
        return f"Error submitting report: {str(e)}. Please ensure your arguments match the required schema."

# Add to tools list
tools.append(submit_research_report)
