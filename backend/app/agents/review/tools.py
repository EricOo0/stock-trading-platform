import logging
import asyncio
from typing import Dict, Any, List
from langchain_core.tools import tool
from backend.app.registry import Tools

logger = logging.getLogger(__name__)
_registry = Tools()

@tool
async def get_review_data(symbol: str) -> Dict[str, Any]:
    """
    Get comprehensive review data including price, history (OHLCV), and technical indicators (including TD Sequential).
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'TSLA').
    """
    try:
        # 1. Get History (Need ~50 days for stable TD Sequential and MA60)
        history = await asyncio.to_thread(_registry.get_historical_data, symbol=symbol, period="3mo")
        
        # 2. Calculate Indicators (using the new advanced calculation with TD Seq)
        # Access the technical_analysis_tool directly from registry to use specific methods if needed,
        # but registry.get_technical_indicators usually calls calculate_advanced_indicators.
        # Let's verify what registry.get_technical_indicators does.
        # It calls tool.calculate_indicators(candles). 
        # Wait, calculate_indicators (legacy) calls calculate_advanced_indicators but returns simplified dict.
        # I need the FULL advanced dict with 'td_sequential'.
        
        # So I should call the tool method directly.
        ta_tool = _registry.technical
        
        if not history or "error" in history:
            return {"error": "Could not fetch historical data"}

        context = ta_tool.calculate_advanced_indicators(history)
        
        # Add basic info
        price_info = await asyncio.to_thread(_registry.get_stock_price, symbol=symbol)
        
        return {
            "price_info": price_info,
            "technical_context": context
        }
    except Exception as e:
        logger.error(f"Error getting review data for {symbol}: {e}")
        return {"error": str(e)}

@tool
async def search_news_for_review(symbol: str) -> str:
    """
    Search for recent news and discussions related to the stock to explain price movements.
    Args:
        symbol: Stock symbol.
    """
    try:
        query = f"{symbol} stock news reason for move today"
        results = await asyncio.to_thread(
            _registry.search_market_news,
            query=query,
            provider="auto",
            topic="news"
        )
        return str(results[:5]) # Return top 5 results
    except Exception as e:
        return f"Error searching news: {str(e)}"

tools = [get_review_data, search_news_for_review]
