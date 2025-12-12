from backend.infrastructure.adk.core.agent_factory import create_agent
from backend.infrastructure.adk.core.tools import get_stock_price, get_financial_metrics

market_agent = create_agent(
    name="MarketDataInvestigator",
    description="Agent for retrieving real-time stock prices and financial metrics.",
    instruction="""
    You are a Market Data Investigator.
    Your goal is to provide accurate stock prices and financial metrics.
    
    Responsibilities:
    1. Retrieve real-time stock quotes using `get_stock_price`.
    2. Get key financial indicators (revenue, profit, PE, etc.) using `get_financial_metrics`.
    
    Always indicate the currency and market (US/HK/A-share) if known.
    """,
    tools=[get_stock_price, get_financial_metrics]
)

