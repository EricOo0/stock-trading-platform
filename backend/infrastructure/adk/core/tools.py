"""
ADK Agent Tools Wrapper

This module provides tool functions for ADK agents by wrapping the tools.registry.Tools class.
Unlike fintech_agent.tools, this directly uses the registry without intermediary wrappers.
"""

import sys
import os
from typing import Optional, Dict, Any, List

import sys
import os
from typing import Optional, Dict, Any, List

from backend.app.registry import Tools

# Global registry instance - will be initialized after environment configuration
_registry: Optional[Tools] = None

def get_registry() -> Tools:
    """
    Get or create the Tools registry singleton.
    This ensures Tools is only initialized once, after environment variables are set.
    """
    global _registry
    if _registry is None:
        _registry = Tools()
    return _registry


# ============================================================================
# Market Data Tools
# ============================================================================

def get_stock_price(symbol: str, market: Optional[str] = None) -> Dict[str, Any]:
    """
    Get real-time stock price for a given symbol.
    
    Args:
        symbol: The stock symbol (e.g., 'AAPL', '0700.HK', 'sh600519').
        market: Optional market ('US', 'HK', 'A-share'). Auto-detected if not provided.
    
    Returns:
        JSON object containing price, change, and percentage.
    """
    return get_registry().get_stock_price(symbol, market)


def get_financial_metrics(symbol: str) -> Dict[str, Any]:
    """
    Get key financial indicators (revenue, profit, PE ratio, etc.) for a company.
    
    Args:
        symbol: The stock symbol.
    
    Returns:
        JSON object with financial metrics.
    """
    return get_registry().get_financial_metrics(symbol)


# ============================================================================
# News & Search Tools
# ============================================================================

def search_market_news(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for latest market news related to a query.
    
    Args:
        query: Search query (e.g., "Apple stock news", "Fed interest rate").
        limit: Number of results to return (default: 5).
    
    Returns:
        List of news items with title and link.
    """
    return get_registry().search_market_news(query, limit=limit)


# ============================================================================
# Macro Economic Data Tools
# ============================================================================

def get_macro_data(query: str) -> Dict[str, Any]:
    """
    Get macro-economic data (GDP, CPI, VIX, etc.).
    
    Args:
        query: The macro indicator to fetch (e.g., "China GDP", "US CPI", "VIX").
    
    Returns:
        JSON object with macro data series.
    """
    return get_registry().get_macro_data(query)


# ============================================================================
# Sentiment Analysis Tools
# ============================================================================

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze the financial sentiment of a text string.
    
    Args:
        text: The text to analyze.
    
    Returns:
        JSON object with sentiment score and label (positive/negative/neutral).
    """
    return get_registry().analyze_sentiment(text)


# ============================================================================
# Financial Report Tools
# ============================================================================

def get_company_report(symbol: str) -> Dict[str, Any]:
    """
    Get metadata about the latest financial report (Annual/Quarterly).
    
    Args:
        symbol: The stock symbol.
    
    Returns:
        JSON object with report title, date, and download URL.
    """
    return get_registry().get_company_report(symbol)


def get_report_content(symbol: str) -> Dict[str, Any]:
    """
    Fetch the text content of the latest financial report.
    This includes fetching the report and extracting text (from PDF or HTML).
    
    Args:
        symbol: The stock symbol.
    
    Returns:
        JSON object with 'content' (str) and 'pdf_url' (str).
    """
    return get_registry().get_report_content(symbol)


def analyze_report(symbol: str) -> Dict[str, Any]:
    """
    Analyze the latest financial report using an LLM to generate a summary and insights.
    
    Args:
        symbol: The stock symbol.
    
    Returns:
        JSON object with 'report' (markdown text), citations, and source URL.
    """
    return get_registry().analyze_report(symbol)


# ============================================================================
# Export all tool functions
# ============================================================================

__all__ = [
    'get_stock_price',
    'get_financial_metrics',
    'search_market_news',
    'get_macro_data',
    'analyze_sentiment',
    'get_company_report',
    'get_report_content',
    'analyze_report',
]
