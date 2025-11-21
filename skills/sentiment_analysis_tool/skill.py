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
    query: str = Field(description="The query to analyze sentiment for, e.g., 'Analyze sentiment for AAPL'")

class SentimentAnalysisSkill(BaseTool):
    """
    Market Sentiment Analysis Skill
    Analyzes market sentiment for specific stocks based on news and social media.
    """
    name: str = "sentiment_analysis_tool"
    description: str = "Analyzes market sentiment for specific stocks based on news and social media."
    args_schema: type[BaseModel] = SentimentAnalysisInput

    _news_service: NewsSearchService = PrivateAttr()
    _sentiment_service: SentimentService = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._news_service = NewsSearchService()
        self._sentiment_service = SentimentService()
        logger.info("Sentiment Analysis Skill initialized")

    def _run(self, query: str) -> Dict[str, Any]:
        """
        Main entry point for the skill.
        
        Args:
            query: User query (e.g., "Analyze sentiment for AAPL")
            
        Returns:
            Dictionary containing sentiment analysis result
        """
        text_input = query
        try:
            logger.info(f"Received sentiment query: {text_input}")
            
            # Extract symbol from text
            symbol = self._extract_symbol(text_input)
            
            if not symbol:
                return {
                    "status": "error",
                    "message": "Could not identify a stock symbol in the query. Please provide a symbol (e.g., AAPL, 000001).",
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
                "symbol": text_input
            }

    async def _arun(self, query: str) -> Dict[str, Any]:
        """Run the tool asynchronously."""
        return self._run(query)

    def _extract_symbol(self, text: str) -> str:
        """Extract stock symbol from text"""
        # Simple extraction logic - similar to market_data_tool but simplified
        # 1. Look for US stocks (AAPL, TSLA)
        us_match = re.search(r'\b[A-Z]{1,5}\b', text)
        if us_match:
            return us_match.group(0)
            
        # 2. Look for A-share/HK codes (6 digits or 5 digits)
        code_match = re.search(r'\b\d{5,6}\b', text)
        if code_match:
            return code_match.group(0)
            
        # 3. Look for common Chinese names (simplified mapping)
        # In a real app, this should share the mapping from market_data_tool
        common_names = {
            "平安银行": "000001", "茅台": "600519", "腾讯": "00700", 
            "阿里": "BABA", "特斯拉": "TSLA", "苹果": "AAPL"
        }
        for name, code in common_names.items():
            if name in text:
                return code
                
        return None

def main_handle(text_input: str) -> Dict[str, Any]:
    """Wrapper function for the skill adapter"""
    skill = SentimentAnalysisSkill()
    return skill._run(text_input)
