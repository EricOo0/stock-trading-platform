#!/usr/bin/env python3
import logging
import datetime
import sys
import time
import requests
import re
import argparse
import json
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("news-sentiment")

# Compatibility patch for snscrape on Python 3.12+
if sys.version_info >= (3, 12):
    import pkgutil
    import importlib.util
    
    # snscrape.modules uses pkgutil.iter_modules which depends on find_module/load_module
    # which were removed in Python 3.12. We monkeypatch them back if needed.
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

HAS_SNSCRAPE = False
try:
    import snscrape.modules.twitter as sntwitter
    import snscrape.modules.reddit as snreddit
    HAS_SNSCRAPE = True
except Exception as e:
    logger.warning(f"Failed to import snscrape: {e}")

HAS_TEXTBLOB = False
try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    logger.warning("TextBlob not found. Sentiment analysis will be disabled.")


class NewsSentimentSkill:
    """
    News and Sentiment Analysis Skill.
    Combines news scraping (Sina Finance) and social media searching (Twitter/Reddit via snscrape),
    along with basic sentiment analysis using TextBlob.
    """
    
    # Sina configuration
    SINA_BASE_URL_NEWS = "https://vip.stock.finance.sina.com.cn"
    SCRAPER_TIMEOUT = 10
    SCRAPER_DELAY = 1.0

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
             'Referer': 'https://finance.sina.com.cn/'
        })
        self.last_request_time = 0

    def _rate_limit(self):
        """Ensure we don't make requests too frequently for scraping"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.SCRAPER_DELAY:
            time.sleep(self.SCRAPER_DELAY - elapsed)
        self.last_request_time = time.time()

    # ========================== News Scraping (Sina) ==========================

    def search_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape news for a stock symbol from Sina Finance.
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.error("beautifulsoup4 not installed.")
            return []

        try:
            sina_symbol = self._convert_to_sina_format_for_news(symbol)
            
            self._rate_limit()
            
            # Example URL: https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_AllNewsStock/symbol/sz000001.phtml
            url = f"{self.SINA_BASE_URL_NEWS}/corp/go.php/vCB_AllNewsStock/symbol/{sina_symbol}.phtml"
            
            logger.info(f"Fetching news from: {url}")
            response = self.session.get(url, timeout=self.SCRAPER_TIMEOUT)
            # Sina usually uses gb2312 for these pages
            response.encoding = 'gb2312'
            
            if response.status_code != 200:
                logger.warning(f"Sina Finance returned status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []
            
            # Selector strategy
            articles = soup.select('div.datelist ul li')
            if not articles:
                 articles = soup.select('div#allNews ul li')

            if articles:
                for article in articles[:limit]:
                    try:
                        link_elem = article.select_one('a')
                        if not link_elem: continue
                        
                        title = link_elem.get_text(strip=True)
                        url_path = link_elem.get('href', '')
                        
                        time_text = article.get_text().replace(title, '').strip()
                        published_at = self._parse_time(time_text)
                        
                        full_url = url_path if url_path.startswith('http') else f"https://finance.sina.com.cn{url_path}"
                        
                        # Fetch content (summary)
                        summary = title
                        if "sina.com.cn" in full_url:
                             content = self._fetch_article_content(full_url)
                             if content:
                                 summary = content[:500] + "..."
                        
                        item = {
                            'title': title,
                            'summary': summary,
                            'source': 'sina',
                            'url': full_url,
                            'published_at': published_at,
                            'sentiment': self.analyze_sentiment(summary)
                        }
                        news_items.append(item)
                    except Exception as e:
                        logger.warning(f"Error parsing article: {e}")
                        continue
                        
            return news_items

        except Exception as e:
            logger.error(f"Sina scraping failed: {e}")
            return []

    def _convert_to_sina_format_for_news(self, symbol: str) -> str:
        # Assume input symbol is raw code e.g. 000001 or sh600001
        if symbol.startswith('sh') or symbol.startswith('sz'): return symbol
        if symbol.isdigit() and len(symbol) == 6:
             # SH Main (60), STAR (688), SH ETF (51, 58)
             if symbol.startswith(('60', '68', '51', '58')): return f"sh{symbol}"
             # SZ Main/ChiNext (00, 30), SZ ETF (15, 16)
             else: return f"sz{symbol}"
        return symbol.lower()

    def _parse_time(self, time_str: str) -> str:
        try:
             # Basic parser, currently just returning current time as placeholder if parsing fails/complex
             # In a real scenario, we'd parse specific formats like 'YYYY-MM-DD' or 'HH:MM'
             return datetime.datetime.now().isoformat()
        except: return ""

    def _fetch_article_content(self, url: str) -> str:
        """Helper to fetch article body"""
        try:
            self._rate_limit()
            from bs4 import BeautifulSoup
            resp = self.session.get(url, timeout=5)
            # Handle encoding
            resp.encoding = requests.utils.get_encodings_from_content(resp.text)[0] if requests.utils.get_encodings_from_content(resp.text) else 'utf-8'
            
            if resp.status_code != 200: return ""
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            content_div = soup.find('div', id='artibody') or soup.find('div', class_='article-content') or soup.find('div', id='articleContent')
            
            if content_div:
                for script in content_div(["script", "style"]):
                    script.extract()
                return content_div.get_text(strip=True)
            return ""
        except Exception:
            return ""

    # ========================== Social Search (snscrape) ==========================

    def search_social(self, query: str, source: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search social media (Twitter/Reddit) for a query.
        """
        if not HAS_SNSCRAPE:
            logger.error("snscrape not available")
            return []
        
        results = []
        if source in ["twitter", "all"]:
            results.extend(self._scrape_twitter(query, limit))
        if source in ["reddit", "all"]:
            results.extend(self._scrape_reddit(query, limit))
            
        # Sort by date descending
        results.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        return results[:limit]

    def _scrape_twitter(self, query: str, limit: int) -> List[Dict[str, Any]]:
        results = []
        try:
            logger.info(f"Scraping Twitter for: {query}")
            scraper = sntwitter.TwitterSearchScraper(query)
            for i, tweet in enumerate(scraper.get_items()):
                if i >= limit: break
                
                content = tweet.rawContent
                item = {
                    "source": "twitter",
                    "content": content,
                    "author": tweet.user.username,
                    "published_at": tweet.date.isoformat(),
                    "url": tweet.url,
                    "metadata": {
                        "likes": tweet.likeCount,
                        "retweets": tweet.retweetCount
                    },
                    "sentiment": self.analyze_sentiment(content)
                }
                results.append(item)
        except Exception as e:
            logger.error(f"Twitter scraping failed: {e}")
        return results

    def _scrape_reddit(self, query: str, limit: int) -> List[Dict[str, Any]]:
        results = []
        try:
            logger.info(f"Scraping Reddit for: {query}")
            scraper = snreddit.RedditSearchScraper(query)
            for i, post in enumerate(scraper.get_items()):
                if i >= limit: break
                
                content = f"{post.title}\n{post.selftext}" if hasattr(post, 'selftext') else post.title
                item = {
                    "source": "reddit",
                    "content": content,
                    "author": post.author if hasattr(post, 'author') else "unknown",
                    "published_at": post.date.isoformat() if hasattr(post, 'date') else datetime.datetime.now().isoformat(),
                    "url": post.url,
                    "metadata": {
                        "score": post.score if hasattr(post, 'score') else 0,
                        "subreddit": post.subreddit if hasattr(post, 'subreddit') else "unknown"
                    },
                    "sentiment": self.analyze_sentiment(content)
                }
                results.append(item)
        except Exception as e:
            logger.error(f"Reddit scraping failed: {e}")
        return results

    # ========================== Sentiment Analysis ==========================

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text using TextBlob.
        Returns {'polarity': float, 'subjectivity': float}
        Polarity: -1.0 (negative) to 1.0 (positive)
        Subjectivity: 0.0 (objective) to 1.0 (subjective)
        """
        if not HAS_TEXTBLOB or not text:
            return {'polarity': 0.0, 'subjectivity': 0.0}
            
        try:
            blob = TextBlob(text)
            return {
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity
            }
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return {'polarity': 0.0, 'subjectivity': 0.0}

def main():
    parser = argparse.ArgumentParser(description="News and Sentiment Skill")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # News command
    news_parser = subparsers.add_parser("news", help="Search news")
    news_parser.add_argument("symbol", help="Stock symbol (e.g. 000001, sh600001)")
    news_parser.add_argument("--limit", type=int, default=5, help="Number of news items")
    
    # Social command
    social_parser = subparsers.add_parser("social", help="Search social media")
    social_parser.add_argument("query", help="Search query")
    social_parser.add_argument("--source", choices=["twitter", "reddit", "all"], default="all", help="Source platform")
    social_parser.add_argument("--limit", type=int, default=5, help="Number of items")
    
    # Sentiment command
    sentiment_parser = subparsers.add_parser("sentiment", help="Analyze sentiment")
    sentiment_parser.add_argument("text", help="Text to analyze")
    
    args = parser.parse_args()
    tool = NewsSentimentSkill()
    
    if args.command == "news":
        results = tool.search_news(args.symbol, args.limit)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
    elif args.command == "social":
        results = tool.search_social(args.query, args.source, args.limit)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
    elif args.command == "sentiment":
        result = tool.analyze_sentiment(args.text)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
