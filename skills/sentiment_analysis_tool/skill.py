import logging
from typing import Dict, Any, List
import re

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from .config import Config
from .services.news_search import NewsSearchService
from .services.sentiment import SentimentService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalysisInput(BaseModel):
    symbol: str = Field(description="Stock symbol to analyze (e.g., 'AAPL', '000001', '600519')")
    query: str = Field(default="", description="Optional query context for the analysis")

class SentimentAnalysisSkill(BaseTool):
    """
    Market Sentiment Analysis Skill
    Analyzes market sentiment for specific stocks based on news and social media.
    """
    name: str = "sentiment_analysis_tool"
    description: str = (
        "Analyzes market sentiment for a specific stock symbol based on news and social media. "
        "Requires a stock symbol (e.g., AAPL, 000001, 600519) as input."
    )
    args_schema: type[BaseModel] = SentimentAnalysisInput

    _news_service: NewsSearchService = PrivateAttr()
    _sentiment_service: SentimentService = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._news_service = NewsSearchService()
        self._sentiment_service = SentimentService()
        logger.info("Sentiment Analysis Skill initialized")

    def _run(self, symbol: str, query: str = "") -> Dict[str, Any]:
        """
        Main entry point for the skill.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL", "000001", "600519")
            query: Optional context query (not used currently)
            
        Returns:
            Dictionary containing sentiment analysis result
        """
        try:
            logger.info(f"Analyzing sentiment for {symbol}...")
            
            if not symbol:
                return {
                    "status": "error",
                    "message": "Stock symbol is required. Please provide a symbol (e.g., AAPL, 000001).",
                    "symbol": None
                }
                
            # 1. Search for news
            logger.info(f"Searching news for {symbol}...")
            news_items = self._news_service.search_news(symbol, limit=Config.SEARCH_RESULT_LIMIT)
            
            # 2. Analyze sentiment
            logger.info(f"Analyzing sentiment for {symbol}...")
            analysis_result = self._sentiment_service.analyze(news_items)
            
            # 3. Construct response
            return {
                "status": "success",
                "symbol": symbol,
                "data": {
                    "score": analysis_result["score"],
                    "rating": analysis_result["rating"],
                    "summary": analysis_result["summary"],
                    "key_drivers": analysis_result["key_drivers"],
                    "news_count": len(news_items),
                    "sentiment_breakdown": analysis_result["sentiment_breakdown"],
                    "recent_news": [
                        {
                            "title": item["title"],
                            "source": item.get("source", "Unknown"),
                            "published_at": item.get("published_at", "")
                        } for item in news_items[:3] # Return top 3 news for context
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return {
                "status": "error",
                "message": f"Internal error during analysis: {str(e)}",
                "symbol": symbol
            }

    async def _arun(self, symbol: str, query: str = "") -> Dict[str, Any]:
        """Run the tool asynchronously."""
        return self._run(symbol, query)

def main_handle(symbol: str, query: str = "") -> Dict[str, Any]:
    """Wrapper function for the skill adapter"""
    skill = SentimentAnalysisSkill()
    return skill._run(symbol, query)
