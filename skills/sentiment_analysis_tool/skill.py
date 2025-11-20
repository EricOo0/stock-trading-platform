import logging
from typing import Dict, Any, List
import re

from .config import Config
from .services.news_search import NewsSearchService
from .services.sentiment import SentimentService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalysisSkill:
    """
    Market Sentiment Analysis Skill
    Analyzes market sentiment for specific stocks based on news and social media.
    """

    def __init__(self):
        self.news_service = NewsSearchService()
        self.sentiment_service = SentimentService()
        logger.info("Sentiment Analysis Skill initialized")

    def main_handle(self, text_input: str) -> Dict[str, Any]:
        """
        Main entry point for the skill.
        
        Args:
            text_input: User query (e.g., "Analyze sentiment for AAPL")
            
        Returns:
            Dictionary containing sentiment analysis result
        """
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
            news_items = self.news_service.search_news(symbol, limit=Config.SEARCH_RESULT_LIMIT)
            
            # 2. Analyze sentiment
            logger.info(f"Analyzing sentiment for {symbol}...")
            analysis_result = self.sentiment_service.analyze(news_items)
            
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
    return skill.main_handle(text_input)
