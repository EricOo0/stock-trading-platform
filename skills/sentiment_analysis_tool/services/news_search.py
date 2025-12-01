import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
from hashlib import md5
from ..config import Config

logger = logging.getLogger(__name__)

class NewsSearchService:
    """Service to search for financial news from multiple sources"""

    def __init__(self):
        self.provider = Config.SEARCH_PROVIDER
        self.api_key = Config.SEARCH_API_KEY
        
        # Lazy load data sources
        self._reddit_fetcher = None
        self._sina_scraper = None

    def search_news(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for news related to the symbol from multiple sources.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', '000001')
            limit: Max number of news items to return
            
        Returns:
            List of news items (dict)
        """
        # If mock mode is enabled, use mock data
        if Config.ENABLE_MOCK:
            logger.info("Mock mode enabled, returning mock news")
            return self._get_mock_news(symbol, limit)
        
        # Try to fetch from real sources
        news_items = []
        
        # 1. Try Reddit (if configured)
        if Config.REDDIT_CLIENT_ID and Config.REDDIT_CLIENT_SECRET:
            try:
                reddit_news = self._fetch_from_reddit(symbol, limit // 2)
                news_items.extend(reddit_news)
                logger.info(f"Fetched {len(reddit_news)} items from Reddit")
            except Exception as e:
                logger.warning(f"Reddit fetch failed: {e}")
        
        # 2. Try Sina Finance scraper (for Chinese stocks) and self._is_chinese_stock(symbol)
        if Config.SINA_ENABLED:
            try:
                sina_news = self._fetch_from_sina(symbol, limit // 2)
                news_items.extend(sina_news)
                logger.info(f"Scraped {len(sina_news)} items from Sina Finance")
            except Exception as e:
                logger.warning(f"Sina scraping failed: {e}")
        
        # 3. If we still don't have enough news, use mock data as fallback
        # if len(news_items) < 3:
        #     logger.warning(f"Only got {len(news_items)} real news items, supplementing with mock data")
        #     mock_news = self._get_mock_news(symbol, limit - len(news_items))
        #     news_items.extend(mock_news)
        
        # Deduplicate and sort
        news_items = self._deduplicate(news_items)
        news_items.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        return news_items[:limit]
    
    def _fetch_from_reddit(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch news from Reddit"""
        if not self._reddit_fetcher:
            from .reddit_fetcher import RedditFetcher
            self._reddit_fetcher = RedditFetcher()
        
        return self._reddit_fetcher.fetch_news(symbol, limit)
    
    def _fetch_from_sina(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch news from Sina Finance"""
        if not self._sina_scraper:
            from .sina_scraper import SinaFinanceScraper
            self._sina_scraper = SinaFinanceScraper()
        
        return self._sina_scraper.scrape_news(symbol, limit)
    
    def _is_chinese_stock(self, symbol: str) -> bool:
        """Check if symbol is a Chinese stock (A-share or HK)"""
        # A-share: 6 digits
        if len(symbol) == 6 and symbol.isdigit():
            return True
        # HK stock: 5 digits starting with 0
        if len(symbol) == 5 and symbol.startswith('0') and symbol.isdigit():
            return True
        return False
    
    def _deduplicate(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate news items based on title"""
        seen = set()
        unique_items = []
        
        for item in news_items:
            # Create hash from title
            title_hash = md5(item['title'].encode()).hexdigest()
            
            if title_hash not in seen:
                seen.add(title_hash)
                unique_items.append(item)
        
        logger.info(f"Deduplicated {len(news_items)} items to {len(unique_items)} unique items")
        return unique_items

    def _get_mock_news(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """Generate mock news data for testing"""
        logger.info(f"Generating mock news for {symbol}")
        
        # Basic templates for mock news
        templates = [
            {
                "title": f"{symbol}发布最新财报，营收超预期",
                "summary": f"{symbol}今日公布了最新季度财报，营收同比增长15%，净利润超出市场预期。分析师普遍维持买入评级。",
                "sentiment": "positive"
            },
            {
                "title": f"行业竞争加剧，{symbol}面临挑战",
                "summary": f"随着新竞争对手的加入，{symbol}在核心市场的份额受到挤压。管理层表示将加大研发投入以保持优势。",
                "sentiment": "negative"
            },
            {
                "title": f"{symbol}召开年度股东大会",
                "summary": f"{symbol}今日召开年度股东大会，审议通过了多项重要议案，包括年度分红方案和董事会换届选举。",
                "sentiment": "neutral"
            },
            {
                "title": f"外资机构增持{symbol}",
                "summary": f"最新数据显示，多家外资机构在过去一个月内增持了{symbol}的股份，显示出对公司长期发展的信心。",
                "sentiment": "positive"
            },
            {
                "title": f"{symbol}股价波动分析",
                "summary": f"受大盘影响，{symbol}近期股价出现波动。技术指标显示当前处于超卖区域，可能存在反弹机会。",
                "sentiment": "neutral"
            }
        ]
        
        news_items = []
        now = datetime.now()
        
        # Generate random news items
        for i in range(limit):
            template = random.choice(templates)
            # Add some randomness to time
            pub_time = now - timedelta(hours=random.randint(1, 48))
            
            news_items.append({
                "title": template["title"],
                "summary": template["summary"],
                "source": random.choice(["新浪财经", "东方财富", "证券时报", "Bloomberg", "Reuters"]),
                "url": "https://example.com/news/123",
                "published_at": pub_time.isoformat(),
                "mock_sentiment": template["sentiment"] # For internal testing/verification
            })
            
        # Sort by time descending
        news_items.sort(key=lambda x: x["published_at"], reverse=True)
        
        return news_items
