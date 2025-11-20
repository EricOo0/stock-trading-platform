import logging
import time
from typing import List, Dict, Any
from datetime import datetime
import re
from ..config import Config

logger = logging.getLogger(__name__)

class SinaFinanceScraper:
    """Scrape stock news from Sina Finance"""
    
    def __init__(self):
        self.base_url = "https://vip.stock.finance.sina.com.cn"
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Ensure we don't make requests too frequently"""
        elapsed = time.time() - self.last_request_time
        if elapsed < Config.SCRAPER_DELAY:
            time.sleep(Config.SCRAPER_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def scrape_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape news for a stock symbol from Sina Finance.
        
        Args:
            symbol: Stock symbol (e.g., '000001', 'sh600519')
            limit: Max number of news items
            
        Returns:
            List of news items
        """
        if not Config.SINA_ENABLED:
            return []
        
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Convert symbol to Sina format
            sina_symbol = self._convert_symbol(symbol)
            
            # Rate limiting
            self._rate_limit()
            
            # Fetch news page - corrected URL structure
            url = f"{self.base_url}/corp/go.php/vCB_AllNewsStock/symbol/{sina_symbol}.phtml"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            logger.info(f"Fetching news from: {url}")
            response = requests.get(url, headers=headers, timeout=Config.SCRAPER_TIMEOUT)
            response.encoding = 'gb2312'  # Sina uses gb2312 encoding
            
            if response.status_code != 200:
                logger.warning(f"Sina Finance returned status {response.status_code}")
                return []
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []
            
            # Strategy 1: Look for specific news containers
            # Try primary selector first
            articles = soup.select('div.datelist ul li')
            
            # Fallback selectors
            if not articles:
                articles = soup.select('div#allNews ul li')
            
            if not articles:
                # Strategy 2: Find all links and filter by patterns
                # Look for links that seem to be news articles
                all_links = soup.find_all('a', href=True)
                
                filtered_links = []
                for link in all_links:
                    href = link['href']
                    text = link.get_text(strip=True)
                    
                    # Filter criteria:
                    # 1. Link contains '/fintech/|/money/|/stock/|/roll/|/chanjing/|/china/'  (news sections)
                    # 2. Text is meaningful (length > 10 chars)
                    # 3. Not navigation links
                    if (len(text) > 10 and 
                        any(section in href for section in ['/fintech/', '/money/', '/stock/', '/roll/', '/chanjing/', '/china/']) and
                        not any(skip in text for skip in ['更多', '>>',  '查看', '资金流向', '盘面异动'])):
                        
                        filtered_links.append(link)
                
                logger.info(f"Strategy 2: Found {len(filtered_links)} potential news links from {len(all_links)} total links")
                
                # Convert links to articles format
                for link in filtered_links[:limit]:
                    try:
                        title = link.get_text(strip=True)
                        url_path = link['href']
                        
                        # Try to find date near the link
                        parent = link.parent
                        time_text = parent.get_text() if parent else ''
                        # Remove title to get time
                        time_text = time_text.replace(title, '').strip()
                        
                        published_at = self._parse_time(time_text)
                        
                        # Build full URL
                        if url_path.startswith('http'):
                            full_url = url_path
                        else:
                            full_url = f"https://finance.sina.com.cn{url_path}"
                        
                        news_items.append({
                            'title': title,
                            'summary': title,
                            'source': '新浪财经',
                            'url': full_url,
                            'published_at': published_at
                        })
                    except Exception as e:
                        logger.warning(f"Error processing link: {e}")
                        continue
            
            else:
                # Original parsing logic for structured news
                logger.info(f"Strategy 1: Found {len(articles)} article elements")
                
                for article in articles[:limit]:
                    try:
                        # Each li contains time text and an <a> link
                        link_elem = article.select_one('a')
                        if not link_elem:
                            continue
                        
                        title = link_elem.get_text(strip=True)
                        url_path = link_elem.get('href', '')
                        
                        # Extract time (text before the <a> tag)
                        time_text = article.get_text()
                        # Remove the title from the text to get just the time
                        time_text = time_text.replace(title, '').strip()
                        
                        # Parse time to ISO format
                        published_at = self._parse_time(time_text)
                        
                        # Build full URL
                        if url_path.startswith('http'):
                            full_url = url_path
                        else:
                            full_url = f"https://finance.sina.com.cn{url_path}"
                        
                        news_items.append({
                            'title': title,
                            'summary': title,  # Sina list doesn't provide summary
                            'source': '新浪财经',
                            'url': full_url,
                            'published_at': published_at
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error parsing article: {e}")
                        continue
            
            logger.info(f"Successfully scraped {len(news_items)} news items from Sina Finance for {symbol}")
            return news_items
            
        except ImportError:
            logger.error("beautifulsoup4 or requests not installed. Please install: pip install beautifulsoup4 requests")
            return []
        except Exception as e:
            logger.error(f"Sina scraper failed: {e}", exc_info=True)
            return []
    
    def _convert_symbol(self, symbol: str) -> str:
        """Convert stock symbol to Sina Finance format"""
        # A-share symbols
        if len(symbol) == 6 and symbol.isdigit():
            if symbol.startswith(('600', '601', '603', '688')):
                return f'sh{symbol}'  # Shanghai
            elif symbol.startswith(('000', '001', '002', '300')):
                return f'sz{symbol}'  # Shenzhen
        
        # If already has prefix, return as is
        if symbol.startswith(('sh', 'sz')) and len(symbol) == 8:
            return symbol
        
        # US stocks (keep as is, but lowercase)
        return symbol.lower()
    
    def _parse_time(self, time_str: str) -> str:
        """Parse Sina time format to ISO format"""
        try:
            # Common formats: "11月20日 15:30" or "15:30" or "2025-11-20 15:30"
            today = datetime.now()
            
            # Format 1: "MM月DD日 HH:MM"
            match = re.search(r'(\d+)月(\d+)日\s+(\d+):(\d+)', time_str)
            if match:
                month, day, hour, minute = match.groups()
                dt = datetime(today.year, int(month), int(day), int(hour), int(minute))
                return dt.isoformat()
            
            # Format 2: "YYYY-MM-DD HH:MM"
            match = re.search(r'(\d{4})-(\d{2})-(\d{2})\s+(\d+):(\d+)', time_str)
            if match:
                year, month, day, hour, minute = match.groups()
                dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
                return dt.isoformat()
            
            # Format 3: Only time "HH:MM", assume today
            match = re.search(r'(\d+):(\d+)', time_str)
            if match:
                hour, minute = match.groups()
                dt = datetime(today.year, today.month, today.day, int(hour), int(minute))
                return dt.isoformat()
            
            # Fallback
            return today.isoformat()
            
        except Exception as e:
            logger.warning(f"Failed to parse time '{time_str}': {e}")
            return datetime.now().isoformat()
