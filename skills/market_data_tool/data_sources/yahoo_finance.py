"""
Yahoo Finance数据源
使用yfinance库获取股票行情数据
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
import time
import logging
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base import BaseDataSource, DataSourceError, DataSourceTimeout, SymbolNotFoundError
# from ..utils.circuit_breaker import circuit_break
from ..models.schemas import StockData, MarketResponse
from ..config import Config

logger = logging.getLogger(__name__)

class YahooFinanceDataSource(BaseDataSource):
    """Yahoo Finance数据源实现类"""

    def __init__(self, timeout: int = 10, enable_rotation: bool = False):
        """
        初始化Yahoo Finance数据源

        Args:
            timeout: 请求超时时间（秒）
            enable_rotation: 是否启用User-Agent轮换
        """
        super().__init__("yahoo", timeout)
        
        # 创建自定义的requests session，用于请求伪装
        self.session = requests.Session()
        self.enable_rotation = enable_rotation
        
        # 设置请求头伪装，防止被封IP
        self._setup_session_headers()
        
        # 配置代理（可选）
        proxies = self._get_proxies()
        if proxies:
            self.session.proxies.update(proxies)
            self.logger.info(f"使用代理配置: {proxies}")
        
        # 配置yfinance使用自定义session
        self._setup_yfinance_session()

    def _setup_session_headers(self):
        """设置session的请求头伪装"""
        if self.enable_rotation:
            user_agent = self._rotate_user_agent()
        else:
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1'
        })
        
        # self.logger.info(f"设置User-Agent: {user_agent[:50]}...")

    def _setup_yfinance_session(self):
        """配置yfinance库使用自定义的requests session"""
        try:
            # 设置yfinance使用我们的自定义session
            import yfinance as yf
            
            # 为yfinance设置自定义session
            if hasattr(yf, 'utils'):
                # 新版本yfinance
                if hasattr(yf.utils, 'session'):
                    yf.utils.session = self.session
            
            # 同时设置全局session（兼容不同版本）
            yf.session = self.session
            
            # 设置请求间隔，避免过于频繁的请求
            self.session.request = self._rate_limited_request
            
            # self.logger.info("成功配置yfinance使用自定义session")
            
        except Exception as e:
            self.logger.warning(f"配置yfinance session失败: {e}")

    def _rate_limited_request(self, method, url, **kwargs):
        """添加请求间隔的请求方法"""
        time.sleep(0.1)  # 100ms间隔，避免过于频繁
        return requests.Session.request(self.session, method, url, **kwargs)

    def _get_proxies(self) -> Dict[str, str]:
        """获取代理配置（可选）"""
        # 可以在这里配置代理服务器
        # 返回格式: {'http': 'http://proxy:port', 'https': 'https://proxy:port'}
        return {}

    def _rotate_user_agent(self) -> str:
        """轮换User-Agent（可选功能）"""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
        ]
        
        import random
        return random.choice(user_agents)

    # @circuit_break("yahoo")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def get_historical_data(self, symbol: str, market: str, period: str = "30d", interval: str = "1d") -> List[Dict[str, Any]]:
        """
        获取股票历史数据

        Args:
            symbol: 股票代码
            market: 市场类型(A-share, US, HK)
            period: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 时间间隔 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            历史数据列表，每个元素包含时间、开高低收量数据
        """
        try:
            self.logger.info(f"正在从Yahoo Finance获取 {symbol} ({market}) 的历史数据，周期: {period}")

            # 根据市场类型转换symbol格式
            yahoo_symbol = self._convert_symbol_for_yahoo(symbol, market)
            self.logger.debug(f"Yahoo Finance符号: {yahoo_symbol}")

            # 获取股票数据
            ticker = yf.Ticker(yahoo_symbol)

            # 获取历史数据
            hist = ticker.history(period=period, interval=interval)
            if hist.empty:
                self.logger.warning(f"未找到 {symbol} 的历史数据")
                return []

            # 转换数据格式（统一单位）
            historical_data = []
            for date, row in hist.iterrows():
                volume_raw = int(row['Volume'])
                # 根据市场类型转换成交量单位
                if market == "A-share":
                    volume_hands = volume_raw // 100  # 转换为手
                else:
                    volume_hands = volume_raw  # 美股港股保持原始股数
                
                historical_data.append({
                    'timestamp': date.to_pydatetime().isoformat(),
                    'open': round(float(row['Open']), 2),  # 统一价格精度
                    'high': round(float(row['High']), 2),
                    'low': round(float(row['Low']), 2),
                    'close': round(float(row['Close']), 2),
                    'volume': volume_hands,
                    'adj_close': round(float(row.get('Adj Close', row['Close'])), 2)
                })

            self.logger.info(f"成功获取 {len(historical_data)} 条历史数据")
            return historical_data

        except Exception as e:
            self.logger.error(f"获取历史数据失败: {str(e)}")
            return []

    # @circuit_break("yahoo")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def get_stock_quote(self, symbol: str, market: str) -> Dict[str, Any]:
        """
        获取股票行情数据

        Args:
            symbol: 股票代码
            market: 市场类型(A-share, US, HK)

        Returns:
            股票行情数据字典
        """
        try:
            self.logger.info(f"正在从Yahoo Finance获取 {symbol} ({market}) 的数据")

            # 根据市场类型转换symbol格式
            yahoo_symbol = self._convert_symbol_for_yahoo(symbol, market)
            self.logger.debug(f"Yahoo Finance符号: {yahoo_symbol}")

            # 获取股票数据
            ticker = yf.Ticker(yahoo_symbol)

            # 获取当前交易日数据
            print("info-----")

            hist = ticker.history(period="2d")
            if hist.empty:
                raise SymbolNotFoundError(symbol, self.name)

            # 获取股票基本信息
            # info = ticker.info
            info = ticker.fast_info
            print("info",info)
            # 获取所有yfinance直接提供的数据，避免自己计算
            fundamental_data = {
                # 直接从yfinance获取，不计算
                'trailing_pe': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'price_to_book': info.get('priceToBook'),
                'trailing_eps': info.get('trailingEps'),
                'book_value': info.get('bookValue'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                'market_cap': info.get('marketCap'),
                'beta': info.get('beta'),
                'dividend_yield': info.get('trailingAnnualDividendYield'),
                'profit_margin': info.get('profitMargins'),
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                # 股本数据
                'shares_outstanding': info.get('sharesOutstanding'),
                'float_shares': info.get('floatShares'),
                'held_percent_insiders': info.get('heldPercentInsiders'),
                'held_percent_institutions': info.get('heldPercentInstitutions'),
                # 成交量数据
                'average_volume': info.get('averageVolume'),
                'average_volume_10days': info.get('averageVolume10days'),
                'average_daily_volume_10day': info.get('averageDailyVolume10Day'),
                # 其他可直接获取的指标
                'current_ratio': info.get('currentRatio'),
                'debt_to_equity': info.get('debtToEquity'),
                'return_on_equity': info.get('returnOnEquity'),
                'return_on_assets': info.get('returnOnAssets'),
                'gross_margins': info.get('grossMargins'),
                'operating_margins': info.get('operatingMargins'),
                'ebitda': info.get('ebitda'),
                'total_debt': info.get('totalDebt'),
                'total_cash': info.get('totalCash'),
                'free_cashflow': info.get('freeCashflow'),
                'operating_cashflow': info.get('operatingCashflow')
            }

            # 解析数据
            current_price = hist['Close'].iloc[-1] if len(hist) > 0 else 0
            previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else info.get('previousClose', 0)
            open_price = hist['Open'].iloc[-1] if len(hist) > 0 else info.get('open', 0)
            high_price = hist['High'].iloc[-1] if len(hist) > 0 else info.get('dayHigh', 0)
            low_price = hist['Low'].iloc[-1] if len(hist) > 0 else info.get('dayLow', 0)
            volume = int(hist['Volume'].iloc[-1]) if len(hist) > 0 else 0

            # 计算涨跌额和涨跌幅
            change_amount = current_price - previous_close
            change_percent = (change_amount / previous_close * 100) if previous_close > 0 else 0

            # 转换成交量单位为手（100股 = 1手）
            volume_hands = volume // 100 if market == "A-share" else volume
            
            # 计算成交额（当前价格 * 成交量）
            turnover = current_price * volume_hands

            # 股票名称
            stock_name = (info.get('longName') or
                         info.get('displayName') or
                         info.get('shortName') or
                         f"{market.upper()}公司")

            result = {
                "symbol": symbol,
                "name": stock_name,
                "current_price": round(float(current_price), 2),
                "open_price": round(float(open_price), 2),
                "high_price": round(float(high_price), 2),
                "low_price": round(float(low_price), 2),
                "previous_close": round(float(previous_close), 2),
                "change_amount": round(float(change_amount), 2),
                "change_percent": round(float(change_percent), 2),
                "volume": volume_hands,
                "turnover": round(float(turnover), 2),
                "timestamp": datetime.now(),
                "market": market,
                "currency": self._get_currency_for_market(market),
                "status": "trading",
                "fundamental_data": fundamental_data  # 添加真实基本面数据
            }

            self.logger.info(f"成功获取 {symbol} 数据: 当前价格 {current_price}")
            return result

        except SymbolNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"获取 {symbol} 数据失败: {str(e)}")
            if "Connection" in str(e) or "Timeout" in str(e):
                raise DataSourceTimeout(self.name, self.timeout)
            else:
                raise DataSourceError(self.name, e)

    def validate_symbol(self, symbol: str, market: str) -> bool:
        """
        验证股票代码是否有效

        Args:
            symbol: 股票代码
            market: 市场类型

        Returns:
            True如果有效，False如果无效
        """
        try:
            # 使用基本验证
            from ..utils import validate_stock_symbol
            return validate_stock_symbol(symbol, market)
        except Exception as e:
            self.logger.warning(f"验证失败 {symbol}: {e}")
            return False

    def _convert_symbol_for_yahoo(self, symbol: str, market: str) -> str:
        """
        转换symbol为Yahoo Finance格式

        Args:
            symbol: 股票代码
            market: 市场类型

        Returns:
            Yahoo格式代码
        """
        if market == "A-share":
            # A股在Yahoo Finance中需要添加.SS或.SZ后缀
            prefix = symbol[:3]
            if prefix in ["600", "601", "603"]:
                return f"{symbol}.SS"  # 上证
            else:
                return f"{symbol}.SZ"  # 深证
        elif market == "US":
            # 美股直接使用代码
            return symbol.upper()
        elif market == "HK":
            # 港股添加.HK后缀
            # 处理港股代码格式：'00700'格式需要转换为'0700'格式（仅限5位数且以'00'开头的代码）
            if symbol.startswith('00') and len(symbol) == 5:
                converted_symbol = symbol[1:]  # 去掉第一个'0'
            else:
                converted_symbol = symbol
            return f"{converted_symbol}.HK"
        else:
            return symbol

    def _get_currency_for_market(self, market: str) -> str:
        """获取市场对应的货币"""
        currencies = {
            "A-share": "CNY",
            "US": "USD",
            "HK": "HKD"
        }
        return currencies.get(market, "CNY")

    def get_market_status(self, market: str) -> Dict[str, Any]:
        """获取市场状态"""
        try:
            # 获取市场指数来判断交易状态
            if market == "A-share":
                index_symbol = "000001.SS"  # 上证指数
            elif market == "US":
                index_symbol = "^GSPC"       # 标普500
            elif market == "HK":
                index_symbol = "^HSI"        # 恒生指数
            else:
                return {"status": "unknown", "market_hours": "unknown"}

            ticker = yf.Ticker(index_symbol)
            hist = ticker.history(period="1d")
            is_trading = not hist.empty

            return {
                "is_trading": is_trading,
                "last_trade_time": hist.index[-1].strftime("%Y-%m-%d %H:%M:%S") if is_trading else None,
                "market_hours": self._get_market_hours(market)
            }

        except Exception as e:
            self.logger.error(f"获取市场状态失败: {e}")
            return {
                "is_trading": False,
                "error": str(e)
            }

    def _get_market_hours(self, market: str) -> str:
        """获取市场交易时间"""
        from ..config import Config
        hours = Config.MARKET_TRADING_HOURS.get(market, {})
        if market == "A-share":
            return f"上午: {hours.get('morning_start', '?')}-{hours.get('morning_end', '?')}, 下午: {hours.get('afternoon_start', '?')}-{hours.get('afternoon_end', '?')}"
        else:
            return f"交易时间: {hours.get('start', '?')}-{hours.get('end', '?')}"

    def test_connection(self) -> bool:
        """测试数据源连接"""
        try:
            # 尝试获取苹果(AAPL)的数据来测试连接
            ticker = yf.Ticker("AAPL")
            info = ticker.fast_info
            return bool(info)
        except Exception as e:
            self.logger.error(f"Yahoo Finance连接测试失败: {e}")
            return False

    def get_data_source_info(self) -> Dict[str, Any]:
        """获取数据源信息"""
        try:
            connection_ok = self.test_connection()
            return {
                "name": self.name,
                "type": "yahoo_finance",
                "status": "connected" if connection_ok else "disconnected",
                "timeout": self.timeout,
                "last_test": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "name": self.name,
                "type": "yahoo_finance",
                "status": "error",
                "error": str(e),
                "last_test": datetime.now().isoformat()
            }


def main():
    """
    测试Yahoo Finance数据源的main函数
    用于验证数据源连接和各项功能
    """
    import json
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("=== Yahoo Finance数据源测试 ===")
    print("💡 提示: 启用User-Agent轮换功能可以更好地防止IP被封")
    
    # 创建数据源实例（启用User-Agent轮换）
    data_source = YahooFinanceDataSource(timeout=15, enable_rotation=True)
    
    # 测试1: 连接测试
    print("\n1. 测试数据源连接...")
    connection_ok = data_source.test_connection()
    print(f"连接状态: {'✅ 正常' if connection_ok else '❌ 失败'}")
    
    if not connection_ok:
        print("数据源连接失败，请检查网络连接")
        return
    
    # 测试2: 获取数据源信息
    print("\n2. 获取数据源信息...")
    info = data_source.get_data_source_info()
    print(f"数据源信息: {json.dumps(info, ensure_ascii=False, indent=2)}")
    
    # 测试3: 获取实时行情（多市场）
    print("\n3. 测试获取实时行情...")
    test_symbols = [
        ("AAPL", "US"),      # 美股 - 苹果
        ("000001", "A-share"),  # A股 - 平安银行
        ("00700", "HK"),     # 港股 - 腾讯控股
        ("MSFT", "US"),      # 美股 - 微软
        ("600036", "A-share")   # A股 - 招商银行
    ]
    
    for symbol, market in test_symbols:
        try:
            print(f"\n获取 {symbol} ({market}) 的实时行情...")
            quote = data_source.get_stock_quote(symbol, market)
            print(f"✅ 成功获取数据:")
            print(f"  - 股票名称: {quote.get('name', 'N/A')}")
            print(f"  - 当前价格: {quote.get('currency', 'USD')}{quote.get('current_price', 'N/A')}")
            print(f"  - 涨跌幅: {quote.get('change_percent', 0):.2f}%")
            print(f"  - 成交量: {quote.get('volume', 0):,}")
            print(f"  - 更新时间: {quote.get('timestamp', 'N/A')}")
            
            # 显示基本面数据（如果有）
            fundamental = quote.get('fundamental_data', {})
            if fundamental:
                key_metrics = []
                if fundamental.get('trailing_pe'):
                    key_metrics.append(f"市盈率: {fundamental['trailing_pe']:.2f}")
                if fundamental.get('market_cap'):
                    key_metrics.append(f"市值: {fundamental['market_cap']:,}")
                if key_metrics:
                    print(f"  - 关键指标: {', '.join(key_metrics)}")
                    
        except Exception as e:
            print(f"❌ 获取 {symbol} 数据失败: {str(e)}")
    
    # 测试4: 获取历史数据（不同周期和间隔）
    print("\n4. 测试获取历史数据...")
    
    # 测试不同的周期和间隔组合
    test_configs = [
        ("AAPL", "US", "7d", "1d"),     # 美股7天日线
        ("000001", "A-share", "30d", "1d"),  # A股30天日线
        ("AAPL", "US", "5d", "1h"),     # 美股5天小时线
        ("AAPL", "US", "1d", "5m"),     # 美股1天5分钟线
    ]
    
    for symbol, market, period, interval in test_configs:
        try:
            print(f"\n测试 {symbol} ({market}) {period} {interval} 数据...")
            historical_data = data_source.get_historical_data(symbol, market, period=period, interval=interval)
            
            if historical_data:
                print(f"✅ 成功获取 {len(historical_data)} 条数据")
                print(f"数据范围: {historical_data[0]['timestamp'][:10]} 到 {historical_data[-1]['timestamp'][:10]}")
                print("最近3条数据:")
                for i, data in enumerate(historical_data[-3:], 1):
                    time_str = data['timestamp'][:19].replace('T', ' ')
                    print(f"  {i}. {time_str}: 开{data['open']:.2f} 高{data['high']:.2f} 低{data['low']:.2f} 收{data['close']:.2f} 量{data['volume']:,}")
            else:
                print("⚠️ 未获取到数据")
                
        except Exception as e:
            print(f"❌ 获取 {symbol} {period} {interval} 数据失败: {str(e)}")
    
    # 测试5: 验证股票代码
    print("\n5. 测试股票代码验证...")
    test_codes = [
        ("AAPL", "US"),
        ("000001", "A-share"),
        ("00700", "HK"),
        ("INVALID", "US"),
        ("12345", "A-share"),
        ("", "US")
    ]
    
    for code, market in test_codes:
        is_valid = data_source.validate_symbol(code, market)
        print(f"  {code} ({market}): {'✅ 有效' if is_valid else '❌ 无效'}")
    
    # 测试6: 获取市场状态
    print("\n6. 测试获取市场状态...")
    test_markets = ["A-share", "US", "HK"]
    
    for market in test_markets:
        try:
            print(f"\n获取 {market} 市场状态...")
            market_status = data_source.get_market_status(market)
            print(f"交易状态: {'🟢 交易中' if market_status.get('is_trading') else '🔴 休市'}")
            if market_status.get('last_trade_time'):
                print(f"最后交易时间: {market_status['last_trade_time']}")
            if market_status.get('market_hours'):
                print(f"交易时间: {market_status['market_hours']}")
        except Exception as e:
            print(f"❌ 获取 {market} 市场状态失败: {str(e)}")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    main()