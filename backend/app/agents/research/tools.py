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


# Export tools list
tools = [
    search_google,
    get_market_data,
    get_macro_economic_data,
    get_technical_indicators,
    get_financial_metrics,
    get_company_report,
    get_discussion_wordcloud,
]
