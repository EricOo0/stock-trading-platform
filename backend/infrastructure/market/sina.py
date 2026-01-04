
import requests
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger(__name__)

class SinaFinanceTool:
    """
    Sina Finance Tool
    Provides market data (quotes, history) and news scraping for A-shares, HK stocks, and US stocks.
    """
    
    # Configuration defaults
    TIMEOUT = 10
    SCRAPER_DELAY = 2.0
    SCRAPER_TIMEOUT = 10
    BASE_URL_HQ = "http://hq.sinajs.cn/"
    BASE_URL_NEWS = "https://vip.stock.finance.sina.com.cn"

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

    # ========================== Market Data ==========================

    def get_stock_quote(self, symbol: str, market: str) -> Dict[str, Any]:
        """
        Get real-time stock quote from Sina Finance.
        Supported markets: A-share, US, HK
        """
        try:
            # Convert symbol to Sina format
            sina_symbol = self._convert_to_sina_format(symbol, market)
            
            # Build URL
            url = f"{self.BASE_URL_HQ}?list={sina_symbol}"
            
            # Request
            response = self.session.get(url, timeout=self.TIMEOUT)
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

            # Parse response
            data = self._parse_sina_response(response.text, symbol, market)
            return data

        except Exception as e:
            logger.error(f"Sina Finance get_stock_quote failed for {symbol}: {e}")
            return {"error": str(e)}

    def get_historical_data(self, symbol: str, market: str, period: str = "30d", interval: str = "1d") -> List[Dict[str, Any]]:
        """
        Get historical data (candlesticks).
        Note: Mostly reliable for A-shares.
        """
        if market != "A-share":
            logger.warning(f"Sina Finance historical data mainly supports A-share, {market} might not work.")
            # We allow it to proceed but it might fail or return empty

        try:
            days = self._parse_period(period)
            scale = self._parse_interval(interval)
            
            sina_symbol = self._convert_to_sina_format(symbol, market)
            
            # Sina K-line API
            hist_url = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
            params = {
                'symbol': sina_symbol,
                'scale': str(scale),
                'ma': 'no',
                'datalen': str(days * 2)
            }
            
            response = self.session.get(hist_url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()
            
            import json
            try:
                data = json.loads(response.text)
            except json.JSONDecodeError:
                data = self._parse_sina_kline_data(response.text)
                
            if not data or not isinstance(data, list):
                return []
            
            historical_data = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for item in data:
                 if isinstance(item, dict) and all(key in item for key in ['day', 'open', 'high', 'low', 'close', 'volume']):
                    try:
                        day_str = item['day']
                        if ' ' in day_str and ':' in day_str:
                             item_date = datetime.strptime(day_str, '%Y-%m-%d %H:%M:%S')
                        else:
                             item_date = datetime.strptime(day_str, '%Y-%m-%d')
                        
                        if item_date >= cutoff_date:
                            historical_data.append({
                                'timestamp': item_date.isoformat(),
                                'open': float(item['open']),
                                'high': float(item['high']),
                                'low': float(item['low']),
                                'close': float(item['close']),
                                'volume': float(item['volume'])
                            })
                    except (ValueError, TypeError):
                        continue
            
            historical_data.sort(key=lambda x: x['timestamp'])
            return historical_data

        except Exception as e:
            logger.error(f"Sina Finance get_historical_data failed for {symbol}: {e}")
            return []

    # ========================== News Scraping ==========================

    def scrape_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape news for a stock symbol.
        """
        try:
            from bs4 import BeautifulSoup
            
            sina_symbol = self._convert_to_sina_format_for_news(symbol) # News URL might use different format sometimes?
            # Actually _convert_to_sina_format should work, but Sina news URL usually uses small letters 'sz', 'sh' for A-share
            
            self._rate_limit()
            
            # Example URL: https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_AllNewsStock/symbol/sz000001.phtml
            url = f"{self.BASE_URL_NEWS}/corp/go.php/vCB_AllNewsStock/symbol/{sina_symbol}.phtml"
            
            logger.info(f"Fetching news from: {url}")
            response = self.session.get(url, timeout=self.SCRAPER_TIMEOUT)
            response.encoding = 'gb2312'
            
            if response.status_code != 200:
                logger.warning(f"Sina Finance returned status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []
            
            # Original scraper logic
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
                        
                        # Fetch content
                        summary = title
                        if "sina.com.cn" in full_url:
                             content = self._fetch_article_content(full_url)
                             if content:
                                 summary = content[:500] + "..."
                        
                        news_items.append({
                            'title': title,
                            'summary': summary,
                            'source': '新浪财经',
                            'url': full_url,
                            'published_at': published_at
                        })
                    except Exception:
                        continue
                        
            return news_items

        except ImportError:
            logger.error("beautifulsoup4 not installed.")
            return []
        except Exception as e:
            logger.error(f"Sina scraping failed: {e}")
            return []

    def _fetch_article_content(self, url: str) -> str:
        """Helper to fetch article body"""
        try:
            time.sleep(0.5)
            from bs4 import BeautifulSoup
            resp = self.session.get(url, timeout=5)
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
            
    # ========================== Helpers ==========================

    def _convert_to_sina_format(self, symbol: str, market: str) -> str:
        if market == "A-share":
            if not symbol.isdigit() or len(symbol) != 6:
                # Try simple heuristic if not standard
                if symbol.startswith('sz') or symbol.startswith('sh'): return symbol
                raise ValueError(f"Invalid A-share symbol: {symbol}")
            
            # SH Main (60), STAR (688), SH ETF (51, 58)
            if symbol.startswith(('60', '68', '51', '58')): return f"sh{symbol}"
            # SZ Main/ChiNext (00, 30), SZ ETF (15, 16)
            else: return f"sz{symbol}" # Default to sz for 000, 002, 300, 159, 161
            
        elif market == "US":
             return f"gb_{symbol.lower()}"
        elif market == "HK":
             # 0700 -> hk00700 (must be 5 digits)
             if len(symbol) == 5 and symbol.isdigit(): return f"hk{symbol}"
             if len(symbol) == 4 and symbol.isdigit(): return f"hk0{symbol}" # Pad with 0?
             if symbol.startswith('0') and len(symbol) == 5: return f"hk{symbol}"
             if symbol.isdigit(): return f"hk{symbol}" # Blindly try
             return f"hk{symbol}"
             
        return symbol

    def _convert_to_sina_format_for_news(self, symbol: str) -> str:
        # For scraping, usually similar to market data
        # Assume input symbol is raw code e.g. 000001 or sh600001
        if symbol.startswith('sh') or symbol.startswith('sz'): return symbol
        if symbol.isdigit() and len(symbol) == 6:
             # Match market logic
             if symbol.startswith(('60', '68', '51', '58')): return f"sh{symbol}"
             else: return f"sz{symbol}"
        return symbol.lower()

    def _parse_sina_response(self, response_text: str, original_symbol: str, market: str) -> Dict[str, Any]:
        match = re.search(r'="([^"]*)"', response_text.strip())
        if not match: raise Exception("Invalid response format")
        content = match.group(1)
        if not content: raise Exception("Empty content")
        fields = content.split(',')

        # Basic parsing logic (simplified from source)
        data = {
            "symbol": original_symbol,
            "market": market,
            "data_source": "sina"
        }
        
        if market == "A-share":
            if len(fields) < 30: raise Exception("Incomplete data")
            data.update({
                "name": fields[0],
                "current_price": float(fields[3]),
                "open": float(fields[1]),
                "prev_close": float(fields[2]),
                "high": float(fields[4]),
                "low": float(fields[5]),
                "volume": float(fields[8]),
                "turnover": float(fields[9]),
                "timestamp": f"{fields[30]} {fields[31]}"
            })
        elif market == "HK":
            if len(fields) < 10: raise Exception("Incomplete data")
            data.update({
                "name": fields[1],
                "current_price": float(fields[6]),
                "prev_close": float(fields[3]),
                "volume": float(fields[12]),
                # ... other fields
            })
        elif market == "US":
            data.update({
                "name": fields[0],
                "current_price": float(fields[1]),
                "prev_close": float(fields[26]) if len(fields) > 26 else 0.0, # Approximate
            })
            
        return data

    def _parse_period(self, period: str) -> int:
        if period.endswith('d'): return int(period[:-1])
        if period.endswith('y'): return int(period[:-1]) * 365
        return 30

    def _parse_interval(self, interval: str) -> int:
        if 'm' in interval: return int(interval.replace('m', ''))
        if 'h' in interval: return 60
        if 'd' in interval: return 240
        return 240

    def _parse_sina_kline_data(self, text: str) -> List[Dict[str, Any]]:
        # Same regex logic as source
        pattern = r'\{[^}]*\}'
        matches = re.findall(pattern, text)
        data = []
        for match in matches:
             try:
                 day = re.search(r'day:"([^"]*)"', match).group(1)
                 close = re.search(r'close:"([^"]*)"', match).group(1)
                 open_ = re.search(r'open:"([^"]*)"', match).group(1)
                 high = re.search(r'high:"([^"]*)"', match).group(1)
                 low = re.search(r'low:"([^"]*)"', match).group(1)
                 vol = re.search(r'volume:"([^"]*)"', match).group(1)
                 data.append({'day': day, 'close': close, 'open': open_, 'high': high, 'low': low, 'volume': vol})
             except Exception: pass
        return data
    
    def _parse_time(self, time_str: str) -> str:
        try:
             # Very basic parser
             return datetime.now().isoformat()
        except: return ""

if __name__ == "__main__":
    tool = SinaFinanceTool()
    # print(tool.get_stock_quote("000001", "A-share"))
    # print(tool.scrape_news("000001", limit=1))
