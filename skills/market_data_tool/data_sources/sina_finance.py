"""
新浪财经数据源备用方案
用于在Yahoo Finance不可用时提供A股数据
"""

import requests
import re
from datetime import datetime, timedelta
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
            period: 时间周期，支持格式如："7d", "30d", "90d", "1y" 等
            interval: 时间间隔，支持："1d"(日线), "1h"(小时线), "30m"(30分钟线), "5m"(5分钟线)
            
        Returns:
            历史数据列表，如果获取失败则返回空列表
        """
        if market not in ["A-share", "US", "HK"]:
            self.logger.warning(f"新浪财经暂不支持{market}市场")
            return []
            
        try:
            self.logger.info(f"正在从新浪财经获取 {symbol} 的历史数据，周期: {period}, 间隔: {interval}")
            
            # 解析时间周期
            days = self._parse_period(period)
            
            # 解析时间间隔
            scale = self._parse_interval(interval)
            
            # 新浪财经的历史数据API
            sina_symbol = self._convert_to_sina_format(symbol, market)
            
            # 新浪财经K线数据接口
            hist_url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
            params = {
                'symbol': sina_symbol,
                'scale': str(scale),  # 时间尺度
                'ma': 'no',
                'datalen': str(days * 2)  # 获取足够的数据，考虑非交易日
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
            
            # 转换数据格式并进行日期过滤
            historical_data = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for item in data:
                if isinstance(item, dict) and all(key in item for key in ['day', 'open', 'high', 'low', 'close', 'volume']):
                    try:
                        # 解析日期时间 - 支持日期和时间格式
                        day_str = item['day']
                        if ' ' in day_str and ':' in day_str:
                            # 包含时间的格式: '2025-11-25 14:00:00'
                            item_date = datetime.strptime(day_str, '%Y-%m-%d %H:%M:%S')
                        else:
                            # 只有日期的格式: '2025-11-25'
                            item_date = datetime.strptime(day_str, '%Y-%m-%d')
                        
                        # 只保留在指定时间范围内的数据
                        if item_date >= cutoff_date:
                            historical_data.append({
                                'timestamp': item_date.isoformat(),
                                'open': float(item['open']),
                                'high': float(item['high']),
                                'low': float(item['low']),
                                'close': float(item['close']),
                                'volume': int(float(item['volume']))
                            })
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"解析数据项失败: {item}, 错误: {e}")
                        continue
            
            # 按日期排序
            historical_data.sort(key=lambda x: x['timestamp'])
            
            self.logger.info(f"成功从新浪财经获取 {len(historical_data)} 条历史数据")
            return historical_data
            
        except Exception as e:
            self.logger.error(f"从新浪财经获取历史数据失败: {str(e)}")
            return []

    def _parse_period(self, period: str) -> int:
        """
        解析时间周期参数
        
        Args:
            period: 时间周期字符串，如 "7d", "30d", "90d", "1y"
            
        Returns:
            对应的天数
        """
        period = period.lower().strip()
        
        if period.endswith('d'):
            days = int(period[:-1])
        elif period.endswith('y'):
            years = int(period[:-1])
            days = years * 365
        elif period.endswith('m'):
            months = int(period[:-1])
            days = months * 30  # 近似值
        else:
            # 默认30天
            days = 30
            
        return min(days, 365 * 5)  # 最多5年数据

    def _parse_interval(self, interval: str) -> int:
        """
        解析时间间隔参数
        
        Args:
            interval: 时间间隔字符串，如 "1d", "1h", "30m", "5m"
            
        Returns:
            新浪财经API对应的时间尺度参数
        """
        interval = interval.lower().strip()
        
        # 新浪财经API的scale参数
        # 1 = 1分钟线, 5 = 5分钟线, 15 = 15分钟线, 30 = 30分钟线
        # 60 = 60分钟线, 240 = 日线, 2400 = 周线
        
        if interval == '1d' or interval == 'd':
            return 240  # 日线
        elif interval == '1h' or interval == 'h':
            return 60   # 小时线
        elif interval == '30m':
            return 30   # 30分钟线
        elif interval == '15m':
            return 15   # 15分钟线
        elif interval == '5m':
            return 5    # 5分钟线
        elif interval == '1m':
            return 1    # 1分钟线
        elif interval == '1w' or interval == 'w':
            return 2400 # 周线
        else:
            return 240  # 默认日线
    
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
        if market not in ["A-share", "US", "HK"]:
            raise DataSourceError(self.name, Exception(f"新浪财经暂不支持{market}市场"))

        try:
            self.logger.info(f"正在从新浪财经获取 {symbol} 的数据")

            # 格式化股票代码
            sina_symbol = self._convert_to_sina_format(symbol, market)

            # 构建请求URL
            url = f"{self.base_url}?list={sina_symbol}"

            # 发送请求 - 需要特定的请求头才能访问新浪财经API
            response = self.session.get(url, timeout=self.timeout, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://finance.sina.com.cn/'
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

    def _convert_to_sina_format(self, symbol: str, market: str = "A-share") -> str:
        """
        将股票代码转换为新浪微博格式

        Args:
            symbol: 股票代码
            market: 市场类型（A-share, US, HK）

        Returns:
            新浪格式代码
        """
        if market == "A-share":
            # A股代码格式验证
            if not symbol.isdigit() or len(symbol) != 6:
                raise ValueError(f"无效的A股代码格式: {symbol}")

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
        
        elif market == "US":
            # 美股代码格式: gb_ + 股票代码小写
            if not symbol.isalpha() or len(symbol) < 1 or len(symbol) > 5:
                raise ValueError(f"无效的美股代码格式: {symbol}")
            return f"gb_{symbol.lower()}"
        
        elif market == "HK":
            # 港股代码格式: hk + 股票代码（5位数字）
            if not symbol.isdigit() or len(symbol) != 5:
                raise ValueError(f"无效的港股代码格式: {symbol}，应为5位数字")
            return f"hk{symbol}"
        
        else:
            raise ValueError(f"不支持的市场类型: {market}")

    # def _parse_sina_response(self, response_text: str, original_symbol: str) -> Dict[str, Any]:
    #     """
    #     解析新浪财经API响应

    #     Args:
    #         response_text: 响应文本
    #         original_symbol: 原始股票代码

    #     Returns:
    #         解析后的股票数据
    #     """
    #     try:
    #         # 新浪财经响应格式：var hq_str_sz000001="平安银行,...
    #         print("response_text:",response_text)
    #         pattern = r'var hq_str_[^=]+="([^"]*)"'
    #         match = re.search(pattern, response_text)
    #         print("match:",match)
    #         if not match:
    #             raise SymbolNotFoundError(original_symbol, self.name)

    #         fields = match.group(1).split(',')

    #         # 检查字段数量
    #         if len(fields) < 33:
    #             raise Exception("返回数据字段不足")

    #         return {
    #             "symbol": original_symbol,
    #             "name": fields[0],  # 股票名称
    #             "current_price": (fields[3]),  # 当前价
    #             "open_price": (fields[1]),     # 开盘价
    #             "previous_close": (fields[2]), # 昨收价
    #             "high_price": (fields[4]),     # 最高价
    #             "low_price": (fields[5]),      # 最低价
    #             "change_amount": (fields[3]) - (fields[2]),  # 涨跌额
    #             "change_percent": ((float(fields[3]) - float(fields[2])) / float(fields[2]) * 100) if float(fields[2]) != 0 else 0.0,
    #             "volume": int(fields[8]),           # 成交量（手）
    #             "turnover": (fields[9]),       # 成交额（万元）
    #             "timestamp": self._parse_chinese_time(fields[30], fields[31]),  # 数据时间
    #             "market": market,
    #             "currency": "CNY",
    #             "status": "trading"
    #         }

    #     except (IndexError, ValueError) as e:
    #         raise Exception(f"解析新浪数据失败: {e}")
    def _parse_sina_response(self, response_text: str, original_symbol: str) -> Dict[str, Any]:
        """
        全能解析：兼容 A股(sh/sz)、港股(hk/rt_hk)、美股(gb_)
        """
        try:
            # 1. 提取 var hq_str_xxx="内容"
            import re
            match = re.search(r'="([^"]*)"', response_text.strip())
            if not match:
                raise SymbolNotFoundError(original_symbol, self.name)

            content = match.group(1)
            if not content:
                raise SymbolNotFoundError(original_symbol, self.name)
            
            fields = content.split(',')
            
            # 2. 识别市场类型
            is_us = "hq_str_gb_" in response_text
            is_hk = "hq_str_hk" in response_text or "hq_str_rt_hk" in response_text
            
            data = {}

            # ================= 🇭🇰 港股解析 (HK) =================
            if is_hk:
                # 港股字段索引 (hk/rt_hk):
                # [0]英文名, [1]中文名, [2]开盘, [3]昨收, [4]最高, [5]最低, [6]当前价
                # [7]涨跌额, [8]涨跌幅, [12]成交量, [13]成交额...
                
                if len(fields) < 10: raise Exception("港股数据字段不足")
                
                name = fields[1] # 中文名
                current_price = float(fields[6])
                prev_close = float(fields[3])
                
                data = {
                    "symbol": original_symbol,
                    "name": name,
                    "current_price": current_price,
                    "open_price": float(fields[2]),
                    "previous_close": prev_close,
                    "high_price": float(fields[4]),
                    "low_price": float(fields[5]),
                    "change_amount": float(fields[7]),
                    "change_percent": float(fields[8]),
                    "volume": int(float(fields[12])), # 某些接口可能返回浮点
                    "turnover": float(fields[11]) if len(fields) > 11 else 0.0,
                    # 港股时间通常在后面，这里简单处理，或者用当前时间
                    "timestamp": f"{fields[17]} {fields[18]}" if len(fields) > 18 else "",
                    "market": "HK",
                    "currency": "HKD"
                }

            # ================= 🇺🇸 美股解析 (US) =================
            elif is_us:
                # 美股字段索引:
                # [0]名, [1]价, [2]幅, [3]时, [4]额, [5]开, [6]高, [7]低
                name = fields[0]
                current_price = float(fields[1])
                change_amount = float(fields[4])
                
                # 倒推昨收
                prev_close = current_price - change_amount
                if len(fields) > 26 and fields[26]:
                    prev_close = float(fields[26])

                data = {
                    "symbol": original_symbol,
                    "name": name,
                    "current_price": current_price,
                    "open_price": float(fields[5]),
                    "previous_close": prev_close,
                    "high_price": float(fields[6]),
                    "low_price": float(fields[7]),
                    "change_amount": change_amount,
                    "change_percent": float(fields[2]),
                    "volume": int(fields[10]),
                    "timestamp": fields[3],
                    "market": "US",
                    "currency": "USD"
                }

            # ================= 🇨🇳 A股解析 (CN) =================
            else:
                # A股字段索引:
                # [0]名, [1]开, [2]昨, [3]现
                if len(fields) < 30: raise Exception("A股数据异常")
                
                current_price = float(fields[3])
                prev_close = float(fields[2])
                
                change_amt = current_price - prev_close
                change_pct = (change_amt / prev_close * 100) if prev_close > 0 else 0.0

                data = {
                    "symbol": original_symbol,
                    "name": fields[0],
                    "current_price": current_price,
                    "open_price": float(fields[1]),
                    "previous_close": prev_close,
                    "high_price": float(fields[4]),
                    "low_price": float(fields[5]),
                    "change_amount": change_amt,
                    "change_percent": change_pct,
                    "volume": int(fields[8]),
                    "turnover": float(fields[9]),
                    "timestamp": f"{fields[30]} {fields[31]}",
                    "market": "A-share",
                    "currency": "CNY"
                }

            # 统一状态处理
            data["status"] = "trading" if data["volume"] > 0 else "suspended"
            return data

        except Exception as e:
            # 打印更详细的错误日志以便调试
            raise Exception(f"解析失败 [{original_symbol}]: {str(e)} | 原文: {response_text[:60]}...")

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
            # if market != "A-share":
            #     return False

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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://finance.sina.com.cn/'
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
                "supported_markets": ["A-share", "US", "HK"],
                "description": "新浪财经备用数据源"
            }
        except Exception as e:
            return {
                "name": self.name,
                "type": "sina_finance",
                "status": "error",
                "error": str(e),
                "last_test": datetime.now().isoformat(),
                "supported_markets": ["A-share", "US", "HK"],
                "description": "新浪财经备用数据源"
            }

    def get_market_data(self, market: str) -> Dict[str, Any]:
        """获取市场数据"""
        # 新浪财经支持的市场类型
        supported_markets = ["A-share", "US", "HK"]
        if market not in supported_markets:
            return {
                "error": f"市场{market}不支持新浪财经数据源",
                "supported_markets": supported_markets
            }

        return {
            "market": market,
            "data_source": self.name,
            "description": f"新浪财经{market}数据源"
        }


def main():
    """
    测试新浪财经数据源的main函数
    用于验证数据源连接和基本功能
    """
    import json
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("=== 新浪财经数据源测试 ===")
    
    # 创建数据源实例
    data_source = SinaFinanceDataSource(timeout=15)
    
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
    
    # 测试3: 获取实时行情
    print("\n3. 测试获取实时行情...")
    test_symbols = ["000001", "600036", "000002"]  # 平安银行、招商银行、万科A
    
    for symbol in test_symbols:
        try:
            print(f"\n获取 {symbol} 的实时行情...")
            quote = data_source.get_stock_quote(symbol, "A-share")
            print(f"✅ 成功获取 {symbol} 数据:")
            print(f"  - 股票名称: {quote.get('name', 'N/A')}")
            print(f"  - 当前价格: ¥{quote.get('current_price', 'N/A')}")
            print(f"  - 涨跌幅: {quote.get('change_percent', 'N/A'):.2f}%")
            print(f"  - 成交量: {quote.get('volume', 'N/A')}手")
            print(f"  - 更新时间: {quote.get('timestamp', 'N/A')}")
        except Exception as e:
            print(f"❌ 获取 {symbol} 数据失败: {str(e)}")
    
    # 测试4: 获取历史数据（支持不同周期和间隔）
    print("\n4. 测试获取历史数据...")
    
    # 测试不同的周期和间隔组合
    test_configs = [
        ("7d", "1d"),    # 7天日线
        ("30d", "1d"),   # 30天日线  
        ("90d", "1d"),   # 90天日线
        ("7d", "1h"),    # 7天小时线
        ("7d", "30m"),   # 7天30分钟线
    ]
    
    for period, interval in test_configs:
        try:
            print(f"\n测试 {period} {interval} 数据...")
            historical_data = data_source.get_historical_data(test_symbols[0], "A-share", period=period, interval=interval)
            
            if historical_data:
                print(f"✅ 成功获取 {len(historical_data)} 条数据")
                print(f"数据范围: {historical_data[0]['timestamp'][:10]} 到 {historical_data[-1]['timestamp'][:10]}")
                print("最近3条数据:")
                for i, data in enumerate(historical_data[-3:], 1):
                    print(f"  {i}. {data['timestamp'][:19]}: 开¥{data['open']:.2f} 收¥{data['close']:.2f} 量{data['volume']:,}")
            else:
                print("⚠️ 未获取到数据")
                
        except Exception as e:
            print(f"❌ 获取 {period} {interval} 数据失败: {str(e)}")
    
    # 测试5: 验证股票代码
    print("\n5. 测试股票代码验证...")
    test_codes = ["000001", "600036", "000002", "300750", "123456", "ABC123"]
    
    for code in test_codes:
        is_valid = data_source.validate_symbol(code, "A-share")
        print(f"  {code}: {'✅ 有效' if is_valid else '❌ 无效'}")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    main()