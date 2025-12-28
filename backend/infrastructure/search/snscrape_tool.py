import logging
import datetime
import sys
from typing import List, Dict, Any, Optional

# Compatibility patch for snscrape on Python 3.12+
if sys.version_info >= (3, 12):
    import pkgutil
    import importlib.util
    
    # snscrape.modules uses pkgutil.iter_modules which depends on find_module/load_module
    # which were removed in Python 3.12. We monkeypatch them back if needed.
    # Note: This is a hack to support the current version of snscrape on 3.12.
    try:
        from _frozen_importlib_external import FileFinder
        if not hasattr(FileFinder, 'find_module'):
            def find_module(self, fullname, path=None):
                spec = self.find_spec(fullname, path)
                if spec is None:
                    return None
                return spec.loader
            FileFinder.find_module = find_module
    except ImportError:
        pass

try:
    import snscrape.modules.twitter as sntwitter
    import snscrape.modules.reddit as snreddit
    HAS_SNSCRAPE = True
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import snscrape: {e}")
    HAS_SNSCRAPE = False

logger = logging.getLogger(__name__)

class SocialScraperTool:
    """
    Social Media Scraper Tool using snscrape.
    Supports Twitter (X) and Reddit.
    """

    def __init__(self):
        if not HAS_SNSCRAPE:
            logger.error("snscrape library not found. Please install it with 'pip install snscrape'.")

    def scrape_twitter(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Scrape tweets for a given query.
        """
        if not HAS_SNSCRAPE:
            return []

        results = []
        try:
            logger.info(f"Scraping Twitter for: {query}")
            # sntwitter.TwitterSearchScraper is the common search entry point
            scraper = sntwitter.TwitterSearchScraper(query)
            for i, tweet in enumerate(scraper.get_items()):
                if i >= limit:
                    break
                results.append({
                    "platform": "twitter",
                    "content": tweet.rawContent,
                    "author": tweet.user.username,
                    "date": tweet.date.isoformat(),
                    "url": tweet.url,
                    "metadata": {
                        "likes": tweet.likeCount,
                        "retweets": tweet.retweetCount,
                        "replies": tweet.replyCount,
                        "quotes": tweet.quoteCount
                    }
                })
        except Exception as e:
            logger.error(f"Twitter scraping failed: {e}")
        
        return results

    def scrape_reddit(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Scrape Reddit posts for a given query.
        """
        if not HAS_SNSCRAPE:
            return []

        results = []
        try:
            logger.info(f"Scraping Reddit for: {query}")
            # snreddit.RedditSearchScraper for searching posts
            scraper = snreddit.RedditSearchScraper(query)
            for i, post in enumerate(scraper.get_items()):
                if i >= limit:
                    break
                results.append({
                    "platform": "reddit",
                    "content": f"{post.title}\n{post.selftext}" if hasattr(post, 'selftext') else post.title,
                    "author": post.author if hasattr(post, 'author') else "unknown",
                    "date": post.date.isoformat() if hasattr(post, 'date') else datetime.datetime.now().isoformat(),
                    "url": post.url,
                    "metadata": {
                        "score": post.score if hasattr(post, 'score') else 0,
                        "comments": post.num_comments if hasattr(post, 'num_comments') else 0,
                        "subreddit": post.subreddit if hasattr(post, 'subreddit') else "unknown"
                    }
                })
        except Exception as e:
            logger.error(f"Reddit scraping failed: {e}")
        
        return results

    def search_all(self, query: str, limit_per_platform: int = 10) -> List[Dict[str, Any]]:
        """
        Search both Twitter and Reddit and return aggregated results.
        """
        twitter_results = self.scrape_twitter(query, limit=limit_per_platform)
        reddit_results = self.scrape_reddit(query, limit=limit_per_platform)
        
        all_results = twitter_results + reddit_results
        # Sort by date descending if possible
        all_results.sort(key=lambda x: x['date'], reverse=True)
        
        return all_results

if __name__ == "__main__":
    # Quick standalone test
    logging.basicConfig(level=logging.INFO)
    scraper = SocialScraperTool()
    
    test_query = "Nvidia"
    print(f"Testing SocialScraperTool with query: {test_query}")
    
    res = scraper.search_all(test_query, limit_per_platform=5)
    import json
    print(json.dumps(res, indent=2, ensure_ascii=False))
