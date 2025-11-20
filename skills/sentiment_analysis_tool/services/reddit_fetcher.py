import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from ..config import Config

logger = logging.getLogger(__name__)

class RedditFetcher:
    """Fetch stock discussions from Reddit"""
    
    def __init__(self):
        self._reddit = None
        self._initialized = False
    
    def _init_reddit(self):
        """Lazy initialize Reddit API client"""
        if self._initialized:
            return
        
        try:
            import praw
            
            # Check if credentials are provided
            if not Config.REDDIT_CLIENT_ID or not Config.REDDIT_CLIENT_SECRET:
                logger.warning("Reddit API credentials not configured. Skipping Reddit.")
                self._initialized = True
                return
            
            self._reddit = praw.Reddit(
                client_id=Config.REDDIT_CLIENT_ID,
                client_secret=Config.REDDIT_CLIENT_SECRET,
                user_agent=Config.REDDIT_USER_AGENT
            )
            
            self._initialized = True
            logger.info("Reddit API client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            self._initialized = True
    
    def fetch_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch Reddit posts about a stock symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')
            limit: Max number of posts to fetch
            
        Returns:
            List of news items
        """
        self._init_reddit()
        
        if not self._reddit:
            return []
        
        try:
            news_items = []
            
            # Target subreddits for financial discussions
            subreddits = ['stocks', 'wallstreetbets', 'investing']
            
            # Search query
            query = f"${symbol} OR {symbol}"
            
            for subreddit_name in subreddits:
                try:
                    subreddit = self._reddit.subreddit(subreddit_name)
                    
                    # Search recent posts (last 7 days)
                    posts = subreddit.search(
                        query=query,
                        time_filter='week',
                        limit=limit // len(subreddits) + 1
                    )
                    
                    for post in posts:
                        # Skip if too old (>3 days)
                        post_age = datetime.utcnow() - datetime.utcfromtimestamp(post.created_utc)
                        if post_age > timedelta(days=3):
                            continue
                        
                        news_items.append({
                            'title': post.title,
                            'summary': post.selftext[:200] if post.selftext else post.title,
                            'source': f'r/{subreddit_name}',
                            'url': f'https://reddit.com{post.permalink}',
                            'published_at': datetime.utcfromtimestamp(post.created_utc).isoformat(),
                            'score': post.score,  # Upvotes - downvotes
                            'num_comments': post.num_comments
                        })
                    
                except Exception as e:
                    logger.warning(f"Error fetching from r/{subreddit_name}: {e}")
                    continue
            
            # Sort by score (most popular first)
            news_items.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            logger.info(f"Fetched {len(news_items)} posts from Reddit for {symbol}")
            return news_items[:limit]
            
        except Exception as e:
            logger.error(f"Reddit fetch failed: {e}")
            return []
