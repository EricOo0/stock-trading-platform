import logging
from typing import Dict, Any, List, Optional
from backend.app.registry import Tools

logger = logging.getLogger(__name__)
# Instantiate registry to access underlying tools
_registry = Tools()

def get_macro_data(query: str) -> Dict[str, Any]:
    """
    Get current macro-economic data snapshot.
    Args:
        query: Query string (e.g., 'China GDP', 'US CPI', 'Fed Rate').
    Returns:
        Dict containing current value and metadata.
    """
    try:
        return _registry.get_macro_data(query)
    except Exception as e:
        logger.error(f"Error fetching macro data for '{query}': {e}")
        return {"error": str(e)}

def get_macro_history(query: str, period: str = "1y") -> Dict[str, Any]:
    """
    Get historical macro-economic data.
    Args:
        query: Query string (e.g., 'China GDP', 'US CPI').
        period: Time period (e.g., '1y', '5y', 'max').
    Returns:
        Dict containing historical time series data.
    """
    try:
        return _registry.get_macro_history(query, period=period)
    except Exception as e:
        logger.error(f"Error fetching macro history for '{query}': {e}")
        return {"error": str(e)}
