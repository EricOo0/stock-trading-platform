import logging
from typing import Dict, Any, List, Optional
from backend.app.registry import Tools

logger = logging.getLogger(__name__)
# Instantiate registry to access underlying tools
_registry = Tools()

def get_stock_price(symbol: str) -> Dict[str, Any]:
    """
    Get real-time stock price and market status.
    Args:
        symbol: Stock symbol (e.g., 'AAPL', '600519', '00700').
    Returns:
        Dict containing price, change, market status, etc.
        Example: {'price': 150.2, 'change_percent': 1.5, 'market': 'US'}
    """
    try:
        return _registry.get_stock_price(symbol)
    except Exception as e:
        logger.error(f"Error fetching stock price for {symbol}: {e}")
        return {"error": str(e)}

def get_historical_data(symbol: str, period: str = "1mo") -> List[Dict[str, Any]]:
    """
    Get historical OHLCV data.
    Args:
        symbol: Stock symbol.
        period: Time period (e.g., '1d', '5d', '1mo', '3mo', '1y').
    Returns:
        List of daily candle data.
    """
    try:
        data = _registry.get_historical_data(symbol, period=period)
        # Limit data size for context window if too large
        if len(data) > 100:
             return data[-100:]
        return data
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        return [{"error": str(e)}]

def get_technical_indicators(symbol: str) -> Dict[str, Any]:
    """
    Get calculated technical indicators (MA, RSI, MACD, etc.).
    Args:
        symbol: Stock symbol.
    Returns:
        Dict of current indicator values.
    """
    try:
        return _registry.get_technical_indicators(symbol)
    except Exception as e:
        logger.error(f"Error fetching technical indicators for {symbol}: {e}")
        return {"error": str(e)}
