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

from .base import BaseDataSource, DataSourceError, DataSourceTimeout, SymbolNotFoundError
from ..utils.circuit_breaker import circuit_break
from ..models.schemas import StockData, MarketResponse
from ..config import Config

logger = logging.getLogger(__name__)

class YahooFinanceDataSource(BaseDataSource):
    """Yahoo Finance数据源实现类"""

    def __init__(self, timeout: int = 10):
        """
        初始化Yahoo Finance数据源

        Args:
            timeout: 请求超时时间（秒）
        """
        super().__init__("yahoo", timeout)

    @circuit_break("yahoo")
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

            # 转换数据格式
            historical_data = []
            for date, row in hist.iterrows():
                historical_data.append({
                    'timestamp': date.to_pydatetime().isoformat(),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']),
                    'adj_close': float(row.get('Adj Close', row['Close']))
                })

            self.logger.info(f"成功获取 {len(historical_data)} 条历史数据")
            return historical_data

        except Exception as e:
            self.logger.error(f"获取历史数据失败: {str(e)}")
            return []

    @circuit_break("yahoo")
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
            hist = ticker.history(period="2d")
            if hist.empty:
                raise SymbolNotFoundError(symbol, self.name)

            # 获取股票基本信息
            info = ticker.info

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

            # 股票名称
            stock_name = (info.get('longName') or
                         info.get('displayName') or
                         info.get('shortName') or
                         f"{market.upper()}公司")

            result = {
                "symbol": symbol,
                "name": stock_name,
                "current_price": float(current_price),
                "open_price": float(open_price),
                "high_price": float(high_price),
                "low_price": float(low_price),
                "previous_close": float(previous_close),
                "change_amount": float(change_amount),
                "change_percent": float(change_percent),
                "volume": volume_hands,
                "turnover": float(current_price * volume),
                "timestamp": datetime.now(),
                "market": market,
                "currency": self._get_currency_for_market(market),
                "status": "trading"
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
            info = ticker.info
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