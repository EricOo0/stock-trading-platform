import os
from typing import Dict, Any

class Config:
    """Configuration for Sentiment Analysis Skill"""
    
    # Search Configuration
    SEARCH_PROVIDER = os.getenv("SENTIMENT_SEARCH_PROVIDER", "reddit")  # reddit, sina, mock
    SEARCH_API_KEY = os.getenv("SENTIMENT_SEARCH_API_KEY", "")
    SEARCH_RESULT_LIMIT = 10
    
    # Reddit API Configuration
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT = "sentiment_analyzer/1.0"
    
    # Scraper Configuration
    SINA_ENABLED = True
    SCRAPER_TIMEOUT = 10
    SCRAPER_DELAY = 2  # Seconds between requests
    
    # LLM Configuration
    LLM_MODEL = "gpt-4o"  # Or whichever model the agent uses
    
    # Mock Data Configuration
    ENABLE_MOCK = os.getenv("ENABLE_MOCK_NEWS", "false").lower() == "true"
