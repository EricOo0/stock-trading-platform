
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from .tools import (
    get_stock_price,
    get_financial_metrics,
    get_company_report,
    get_report_content,
    analyze_report,
    search_market_news,
    get_macro_data,
    analyze_sentiment
)

# Define the Fintech Agent
fintech_agent = Agent(
    model='gemini-2.0-flash', # Using Gemini 2.0 Flash as in google_agent example
    name='FintechAgent',
    instruction="""
    You are a sophisticated Fintech Assistant capable of providing real-time market data, 
    analyzing financial reports, and performing in-depth market research.
    
    Capabilities:
    1.  **Market Data**: Use `get_stock_price` and `get_market_data` for quotes and macro indicators.
    2.  **Financials**: Use `get_financial_metrics` for fundamental data.
    3.  **Reports**: Use `get_company_report` to find reports, `get_report_content` to read them, 
        and `analyze_report` to generate professional summaries with citations.
    4.  **News**: Use `search_market_news` for latest updates.
    5.  **Sentiment**: Use `analyze_sentiment` to gauge market mood.

    Always synthesize information from these tools to provide a comprehensive answer.
    When analyzing reports, rely on the `analyze_report` tool for detailed insights.
    If a user asks about a specific stock, try to provide its current price and recent news context.
    """,
    tools=[
        get_stock_price,
        get_financial_metrics,
        get_company_report,
        get_report_content,
        analyze_report,
        search_market_news,
        get_macro_data,
        analyze_sentiment
    ],
)
