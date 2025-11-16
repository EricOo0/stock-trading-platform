"""
新浪财经数据源备用方案
用于在Yahoo Finance不可用时提供A股数据
"""

import requests
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import time
import logging

from .base import BaseDataSource, DataSourceError, DataSourceTimeout, SymbolNotFoundError
from ..config import Config

logger = logging.getLogger(__name__)

class SinaFinanceDataSource(BaseDataSource):
    """新浪财经数据源实现类"""

    def __init__(self, timeout: int = 10):
        """
        初始化新浪财经数据源

        Args:
            timeout: 请求超时时间（秒）
        """
        super().__init__("sina", timeout)
        self.base_url = "http://hq.sinajs.cn/"
        self.session = requests.Session()

    def get_historical_data(self, symbol: str, market: str, period: str = "30d", interval: str = "1d") -> List[Dict[str, Any]]:
        """
        获取A股历史数据（新浪财经备用数据源）
        
        Args:
            symbol: 股票代码
            market: 市场类型（必须为A-share）
            period: 时间周期（暂时不支持，返回最近30天数据）
            interval: 时间间隔（暂时只支持日线）
            
        Returns:
            历史数据列表，如果获取失败则返回空列表
        """
        if market != "A-share":
            self.logger.warning(f"新浪财经只支持A股数据，不支持{market}市场")
            return []
            
        try:
            self.logger.info(f"正在从新浪财经获取 {symbol} 的历史数据")
            
            # 新浪财经的历史数据API（简化版本，获取最近30个交易日数据）
            # 使用新浪的日线历史数据接口
            sina_symbol = self._convert_to_sina_format(symbol)
            
            # 构造历史数据URL（获取最近30天数据）
            import datetime
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=60)  # 获取60天数据，确保有足够的交易日
            
            # 新浪财经K线数据接口
            hist_url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
            params = {
                'symbol': sina_symbol,
                'scale': '240',  # 日线
                'ma': 'no',
                'datalen': '30'  # 获取30天数据
            }
            
            response = self.session.get(hist_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # 解析返回的JSON数据
            import json
            try:
                data = json.loads(response.text)
            except json.JSONDecodeError:
                # 如果返回的不是标准JSON，尝试解析新浪特有的格式
                data = self._parse_sina_kline_data(response.text)
                
            if not data or not isinstance(data, list):
                self.logger.warning(f"未找到 {symbol} 的历史数据或数据格式错误")
                return []
            
            # 转换数据格式
            historical_data = []
            for item in data:
                if isinstance(item, dict) and all(key in item for key in ['day', 'open', 'high', 'low', 'close', 'volume']):
                    try:
                        historical_data.append({
                            'timestamp': datetime.datetime.strptime(item['day'], '%Y-%m-%d').isoformat(),
                            'open': float(item['open']),
                            'high': float(item['high']),
                            'low': float(item['low']),
                            'close': float(item['close']),
                            'volume': int(float(item['volume']))
                        })
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"解析数据项失败: {item}, 错误: {e}")
                        continue
            
            self.logger.info(f"成功从新浪财经获取 {len(historical_data)} 条历史数据")
            return historical_data
            
        except Exception as e:
            self.logger.error(f"从新浪财经获取历史数据失败: {str(e)}")
            return []
    
    def _parse_sina_kline_data(self, text: str) -> List[Dict[str, Any]]:
        """
        解析新浪K线数据格式
        新浪返回的数据有时是JavaScript对象格式，需要特殊处理
        """
        try:
            # 尝试清理和解析数据
            import re
            import datetime
            
            # 提取数据对象
            pattern = r'\{[^}]*\}'
            matches = re.findall(pattern, text)
            
            data = []
            for match in matches:
                try:
                    # 提取各个字段
                    day_match = re.search(r'day:"([^"]*)"', match)
                    open_match = re.search(r'open:"([^"]*)"', match)
                    high_match = re.search(r'high:"([^"]*)"', match)
                    low_match = re.search(r'low:"([^"]*)"', match)
                    close_match = re.search(r'close:"([^"]*)"', match)
                    volume_match = re.search(r'volume:"([^"]*)"', match)
                    
                    if all([day_match, open_match, high_match, low_match, close_match, volume_match]):
                        data.append({
                            'day': day_match.group(1),
                            'open': open_match.group(1),
                            'high': high_match.group(1),
                            'low': low_match.group(1),
                            'close': close_match.group(1),
                            'volume': volume_match.group(1)
                        })
                except (ValueError, AttributeError):
                    continue
                    
            return data
        except Exception as e:
            self.logger.error(f"解析新浪K线数据失败: {str(e)}")
            return []

    def get_stock_quote(self, symbol: str, market: str) -> Dict[str, Any]:
        """
        获取A股股票行情数据

        Args:
            symbol: 股票代码
            market: 市场类型（必须为A-share）

        Returns:
            股票行情数据字典
        """
        if market != "A-share":
            raise DataSourceError(self.name, Exception(f"新浪财经只支持A股数据，不支持{market}市场"))

        try:
            self.logger.info(f"正在从新浪财经获取 {symbol} 的数据")

            # 格式化股票代码
            sina_symbol = self._convert_to_sina_format(symbol)

            # 构建请求URL
            url = f"{self.base_url}?list={sina_symbol}"

            # 发送请求
            response = self.session.get(url, timeout=self.timeout, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            if response.status_code != 200:
                raise DataSourceError(self.name, Exception(f"HTTP {response.status_code}: {response.text}"))

            # 解析响应数据
            data = self._parse_sina_response(response.text, symbol)

            self.logger.info(f"成功获取新浪财经 {symbol} 数据: 当前价格 {data['current_price']}")
            return data

        except requests.exceptions.Timeout:
            raise DataSourceTimeout(self.name, self.timeout)
        except requests.exceptions.RequestException as e:
            raise DataSourceError(self.name, e)
        except Exception as e:
            self.logger.error(f"新浪财经获取 {symbol} 数据失败: {str(e)}")
            raise DataSourceError(self.name, e)

    def _convert_to_sina_format(self, symbol: str) -> str:
        """
        将A股代码转换为新浪微博格式

        Args:
            symbol: A股代码（6位数字）

        Returns:
            新浪格式代码
        """
        if not symbol.isdigit() or len(symbol) != 6:
            raise ValueError(f"无效的股票代码格式: {symbol}")

        # 根据代码前缀判断市场
        prefix = symbol[:3]
        if prefix in ["000", "002", "300"]:
            # 深证市场
            return f"sz{symbol}"
        elif prefix in ["600", "601", "603"]:
            # 上海市场
            return f"sh{symbol}"
        else:
            raise ValueError(f"不支持的A股代码前缀: {prefix}")

    def _parse_sina_response(self, response_text: str, original_symbol: str) -> Dict[str, Any]:
        """
        解析新浪财经API响应

        Args:
            response_text: 响应文本
            original_symbol: 原始股票代码

        Returns:
            解析后的股票数据
        """
        try:
            # 新浪财经响应格式：var hq_str_sz000001="平安银行,...
            pattern = r'var hq_str_[^=]+="([^"]*)"'
            match = re.search(pattern, response_text)

            if not match:
                raise SymbolNotFoundError(original_symbol, self.name)

            fields = match.group(1).split(',')

            # 检查字段数量
            if len(fields) < 33:
                raise Exception("返回数据字段不足")

            return {
                "symbol": original_symbol,
                "name": fields[0],  # 股票名称
                "current_price": float(fields[3]),  # 当前价
                "open_price": float(fields[1]),     # 开盘价
                "previous_close": float(fields[2]), # 昨收价
                "high_price": float(fields[4]),     # 最高价
                "low_price": float(fields[5]),      # 最低价
                "change_amount": float(fields[3]) - float(fields[2]),  # 涨跌额
                "change_percent": ((float(fields[3]) - float(fields[2])) / float(fields[2]) * 100) if float(fields[2]) != 0 else 0.0,
                "volume": int(fields[8]),           # 成交量（手）
                "turnover": float(fields[9]),       # 成交额（万元）
                "timestamp": self._parse_chinese_time(fields[30], fields[31]),  # 数据时间
                "market": "A-share",
                "currency": "CNY",
                "status": "trading"
            }

        except (IndexError, ValueError) as e:
            raise Exception(f"解析新浪数据失败: {e}")

    def _parse_chinese_time(self, date_str: str, time_str: str) -> datetime:
        """
        解析中文字符串为datetime对象

        Args:
            date_str: 日期字符串 (如 "2025-11-09")
            time_str: 时间字符串 (如 "15:30:00")

        Returns:
            datetime对象
        """
        try:
            datetime_str = f"{date_str} {time_str}"
            return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # 如果格式不匹配，返回当前时间
            self.logger.warning(f"时间解析失败，使用默认时间: {date_str} {time_str}")
            return datetime.now()

    def validate_symbol(self, symbol: str, market: str) -> bool:
        """验证股票代码是否有效"""
        try:
            # 仅支持A股
            if market != "A-share":
                return False

            from ..utils import validate_stock_symbol
            return validate_stock_symbol(symbol, market)
        except Exception:
            return False

    def test_connection(self) -> bool:
        """测试数据源连接"""
        """测试新浪财经连接"""
        try:
            # 使用工商银行测试连接
            test_url = f"{self.base_url}?list=sh601398"
            response = self.session.get(test_url, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            if response.status_code == 200:
                # 进一步验证返回格式
                data = self._parse_sina_response(response.text, "601398")
                return bool(data.get('name'))
            else:
                return False

        except Exception as e:
            self.logger.error(f"新浪财经连接测试失败: {e}")
            return False

    def get_data_source_info(self) -> Dict[str, Any]:
        """获取数据源信息"""
        """获取数据源信息"""
        try:
            connection_ok = self.test_connection()
            return {
                "name": self.name,
                "type": "sina_finance",
                "status": "connected" if connection_ok else "disconnected",
                "timeout": self.timeout,
                "last_test": datetime.now().isoformat(),
                "supported_markets": ["A-share"],
                "description": "新浪财经备用数据源"
            }
        except Exception as e:
            return {
                "name": self.name,
                "type": "sina_finance",
                "status": "error",
                "error": str(e),
                "last_test": datetime.now().isoformat(),
                "supported_markets": ["A-share"],
                "description": "新浪财经备用数据源"
            }

    def get_market_data(self, market: str) -> Dict[str, Any]:
        """获取市场数据"""
        # 新浪财经不支持市场数据查询
        if market != "A-share":
            return {
                "error": f"市场{market}不支持新浪财经数据源",
                "supported_markets": ["A-share"]
            }

        return {
            "market": "A-share",
            "data_source": self.name,
            "description": "新浪财经A股数据源"
        }