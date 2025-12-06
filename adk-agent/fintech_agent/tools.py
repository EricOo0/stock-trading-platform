
import sys
import os
from typing import Optional

# Ensure we can import from the root tools directory
# Assuming we are running from root or adk-agent/
# This path hack handles running from adk-agent root or project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from tools.registry import Tools

# Initialize the registry once
registry = Tools()

def get_stock_price(symbol: str, market: Optional[str] = None):
    """
    Get real-time stock price for a given symbol.
    
    Args:
        symbol: The stock symbol (e.g., 'AAPL', '0700.HK', 'sh600519').
        market: Optional market ('US', 'HK', 'A-share'). If not provided, it is auto-detected.
    
    Returns:
        JSON object containing price, change, and percentage.
    """
    return registry.get_stock_price(symbol, market)

def get_financial_metrics(symbol: str):
    """
    Get key financial indicators (revenue, profit, PE ratio, etc.) for a company.
    
    Args:
        symbol: The stock symbol.
    
    Returns:
        JSON object with financial metrics.
    """
    return registry.get_financial_metrics(symbol)

def get_company_report(symbol: str):
    """
    Get metadata about the latest financial report (Annual/Quarterly).
    
    Args:
        symbol: The stock symbol.
    
    Returns:
        JSON object with report title, date, and download URL.
    """
    return registry.get_company_report(symbol)

def get_report_content(symbol: str):
    """
    Fetch the text content of the latest financial report.
    This includes fetching the report and extracting text (from PDF or HTML).
    
    Args:
        symbol: The stock symbol.
        
    Returns:
        JSON object with 'content' (str) and 'pdf_url' (str).
    """
    return registry.get_report_content(symbol)

def analyze_report(symbol: str):
    """
    Analyze the latest financial report using an LLM to generate a summary and insights.
    
    Args:
        symbol: The stock symbol.
        
    Returns:
        JSON object with 'report' (markdown text), citations, and source URL.
    """
    return registry.analyze_report(symbol)

def search_market_news(query: str):
    """
    Search for latest market news related to a query.
    
    Args:
        query: Search query (e.g., "Apple stock news", "Fed interest rate").
        
    Returns:
        List of news items with title and link.
    """
    return registry.search_market_news(query)

def get_macro_data(query: str):
    """
    Get macro-economic data (GDP, CPI, VIX, etc.).
    
    Args:
        query: The macro indicator to fetch (e.g., "China GDP", "US CPI", "VIX").
        
    Returns:
        JSON object with macro data series.
    """
    return registry.get_macro_data(query)

def analyze_sentiment(text: str):
    """
    Analyze the financial sentiment of a text string.
    
    Args:
        text: The text to analyze.
        
    Returns:
        JSON object with sentiment score and label (positive/negative/neutral).
    """
    return registry.analyze_sentiment(text)
