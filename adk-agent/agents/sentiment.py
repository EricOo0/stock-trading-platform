from core.agent_factory import create_agent
from core.tools import analyze_sentiment

sentiment_agent = create_agent(
    name="SentimentInvestigator",
    description="Agent for analyzing market sentiment from text.",
    instruction="""
    You are a Sentiment Investigator.
    Your goal is to analyze the emotional tone and sentiment of financial text.
    
    Use `analyze_sentiment` to score text as Positive, Negative, or Neutral.
    If given a headline or a paragraph, strictly analyze its sentiment.
    """,
    tools=[analyze_sentiment]
)

