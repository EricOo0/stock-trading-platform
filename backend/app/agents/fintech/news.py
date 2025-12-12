from backend.infrastructure.adk.core.agent_factory import create_agent
from backend.infrastructure.adk.core.tools import search_market_news

news_agent = create_agent(
    name="NewsInvestigator",
    description="Agent for searching latest market news.",
    instruction="""
    You are a News Investigator.
    Your goal is to find the latest and most relevant news for a company or topic.
    
    Use `search_market_news` to find articles.
    Summarize the headlines and key findings from the search results.
    Provide links to the articles if available.
    """,
    tools=[search_market_news]
)

