"""
数据验证模块
提供股票代码、市场数据等验证功能
"""

import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ValidationResult:
    """验证结果类"""

    def __init__(self, is_valid: bool = True, errors: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []

    def add_error(self, error: str):
        """添加错误"""
        self.is_valid = False
        self.errors.append(error)

    def merge(self, other: 'ValidationResult'):
        """合并验证结果"""
        if not other.is_valid:
            self.is_valid = False
            self.errors.extend(other.errors)

    def get_errors(self) -> List[str]:
        """获取错误列表"""
        return self.errors.copy()

    def __bool__(self):
        """布尔值转换"""
        return self.is_valid

    def __str__(self):
        """字符串表示"""
        if self.is_valid:
            return "验证通过"
        return f"验证失败: {'; '.join(self.errors)}"

class StockSymbolValidator:
    """股票代码验证器"""

    # A股代码前缀规则
    A_SHARE_PREFIXES = [
        "000",  # 深证主板
        "001",  # 深证主板
        "002",  # 深证中小板
        "300",  # 创业板
        "600",  # 上证主板
        "601",  # 上证主板
        "603"   # 上证主板
    ]

    # 常见美股代码验证
    COMMON_US_STOCKS = {
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "BRK.A", "BRK.B",
        "JPM", "JNJ", "V", "PG", "UNH", "HD", "MA", "DIS", "PYPL", "ADBE", "CRM", "ORCL",
        "NKE", "BAC", "KO", "PEP", "INTC", "AMD", "CSCO", "VZ", "XOM", "CVX", "WMT", "MCD"
    }

    # 常见港股代码示例
    COMMON_HK_STOCKS = {
        "00700",  # 腾讯控股
        "02318",  # 中国平安
        "09988",  # 阿里巴巴
        "03690",  # 美团
        "01810",  # 小米集团
        "09868",  # 小鹏汽车
        "02020",  # 安踏体育
        "00388",  # 香港交易所
        "00005",  # 汇丰控股
    }

    @classmethod
    def validate_a_share(cls, symbol: str) -> ValidationResult:
        """验证A股代码"""
        result = ValidationResult()

        # 基本格式验证
        if not re.match(r'^\d{6}$', symbol):
            result.add_error(f"A股代码{symbol}必须是6位数字")
            return result

        # 前缀验证
        prefix = symbol[:3]
        if prefix not in cls.A_SHARE_PREFIXES:
            result.add_error(
                f"A股代码{symbol}前缀{prefix}无效，有效前缀为：{', '.join(cls.A_SHARE_PREFIXES)}"
            )

        # 数值范围验证
        try:
            numeric_part = int(symbol[3:])
            # Allow numeric_part to be 0, which is valid (like 600000)
            pass
        except ValueError:
            result.add_error(f"A股代码{symbol}后3位必须是数字")

        return result

    @classmethod
    def validate_us_stock(cls, symbol: str) -> ValidationResult:
        """验证美股代码"""
        result = ValidationResult()

        # 基本格式验证
        if not re.match(r'^[A-Za-z]{1,5}$', symbol):
            result.add_error(f"美股代码{symbol}必须是1-5位字母")
            return result

        # 标准化为大写
        symbol = symbol.upper()

        # 常见股票代码检查（可选，用于提示）
        if symbol in cls.COMMON_US_STOCKS:
            logger.debug(f"美股代码{symbol}属于常见股票")
        else:
            logger.debug(f"美股代码{symbol}不是常见股票，但仍可能有效")

        return result

    @classmethod
    def validate_hk_stock(cls, symbol: str) -> ValidationResult:
        """验证港股代码"""
        result = ValidationResult()

        # 基本格式验证
        if not re.match(r'^0\d{4}$', symbol):
            result.add_error(f"港股代码{symbol}必须是5位数字且以0开头")
            return result

        # 数值范围验证
        numeric_part = int(symbol[1:])
        if numeric_part < 1 or numeric_part > 9999:
            result.add_error(f"港股代码{symbol}后4位必须在0001-9999范围内")

        return result

    @classmethod
    def validate(cls, symbol: str, market: Optional[str] = None) -> ValidationResult:
        """
        验证股票代码

        Args:
            symbol: 股票代码
            market: 市场类型（自动检测如果为None）

        Returns:
            验证结果
        """
        if not symbol or not isinstance(symbol, str):
            result = ValidationResult()
            result.add_error("股票代码不能为空且必须是字符串")
            return result

        symbol = symbol.strip().upper()

        if not market:
            market = cls.detect_market(symbol)

        if market == "A-share":
            return cls.validate_a_share(symbol)
        elif market == "US":
            return cls.validate_us_stock(symbol)
        elif market == "HK":
            return cls.validate_hk_stock(symbol)
        else:
            result = ValidationResult()
            result.add_error(f"不支持的市场类型: {market}")
            return result

    @classmethod
    def detect_market(cls, symbol: str) -> Optional[str]:
        """
        自动检测股票代码所属市场

        Args:
            symbol: 股票代码

        Returns:
            市场类型或None
        """
        symbol = str(symbol).strip().upper()

        # A股: 6位数字，特定前缀开头
        if re.match(r'^\d{6}$', symbol):
            prefix = symbol[:3]
            if prefix in cls.A_SHARE_PREFIXES:
                return "A-share"

        # 美股: 1-5位字母
        if re.match(r'^[A-Z]{1,5}$', symbol):
            return "US"

        # 港股: 5位数字，以0开头
        if re.match(r'^0\d{4}$', symbol):
            return "HK"

        return None

class PriceDataValidator:
    """价格数据验证器"""

    @classmethod
    def validate_price_data(cls, data: Dict[str, Any]) -> ValidationResult:
        """验证价格数据完整性"""
        result = ValidationResult()

        # 检查必需字段
        required_fields = ["current_price", "open_price", "high_price", "low_price", "previous_close", "volume"]
        for field in required_fields:
            if field not in data:
                result.add_error(f"缺少必需字段: {field}")

        if not result:
            return result  # 有错误则直接返回

        current = data["current_price"]
        open_price = data["open_price"]
        high = data["high_price"]
        low = data["low_price"]
        previous = data["previous_close"]
        volume = data["volume"]

        # 价格正数验证
        if current <= 0:
            result.add_error(f"当前价格必须大于0，当前值: {current}")

        if open_price <= 0:
            result.add_error(f"开盘价必须大于0，当前值: {open_price}")

        if high <= 0:
            result.add_error(f"最高价必须大于0，当前值: {high}")

        if low <= 0:
            result.add_error(f"最低价必须大于0，当前值: {low}")

        if previous <= 0:
            result.add_error(f"昨收价必须大于0，当前值: {previous}")

        # 价格关系验证
        if high < low:
            result.add_error(f"最高价({high})不能低于最低价({low})")

        if not (low <= current <= high):
            result.add_error(f"当前价格({current})必须在最高价({high})和最低价({low})范围内")

        if not (low <= open_price <= high):
            result.add_error(f"开盘价({open_price})必须在最高价({high})和最低价({low})范围内")

        # 成交量验证
        if volume < 0:
            result.add_error(f"成交量不能为负数，当前值: {volume}")

        # 计算验证
        expected_change = current - previous
        actual_change = data.get("change_amount", expected_change)
        if abs(expected_change - actual_change) > 0.01:
            result.add_error(f"涨跌额计算错误: 期望{expected_change:.2f}，实际{actual_change:.2f}")

        # 涨跌幅验证
        if previous > 0:
            expected_change_percent = (expected_change / previous) * 100
            actual_change_percent = data.get("change_percent", expected_change_percent)
            if abs(expected_change_percent - actual_change_percent) > 0.1:
                result.add_error(
                    f"涨跌幅计算错误: 期望{expected_change_percent:.2f}%，实际{actual_change_percent:.2f}%"
                )

        return result

    @classmethod
    def validate_price_reasonableness(cls, data: Dict[str, Any]) -> ValidationResult:
        """验证价格合理性"""
        result = ValidationResult()

        change_percent = data.get("change_percent", 0)

        # 涨跌幅合理性检查
        if abs(change_percent) > 20:  # A股涨跌停限制约为20%
            result.add_error(f"涨跌幅{change_percent:.2f}%超出正常范围(±20%)")

        return result

class TimeDataValidator:
    """时间数据验证器"""

    @classmethod
    def validate_timestamp(cls, timestamp: datetime, max_age: int = 60,
                          market: Optional[str] = None) -> ValidationResult:
        """
        验证时间戳有效性

        Args:
            timestamp: 时间戳
            max_age: 最大允许时间差（分钟）
            market: 市场类型

        Returns:
            验证结果
        """
        result = ValidationResult()

        # 基本类型验证
        if not isinstance(timestamp, datetime):
            result.add_error("时间戳必须是datetime类型")
            return result

        now = datetime.now()

        # 未来时间检查
        if timestamp > now:
            result.add_error(f"时间戳{timestamp}不能是未来时间")

        # 时间差检查
        age = (now - timestamp).total_seconds() / 60  # 分钟
        if age > max_age:
            result.add_error(f"时间戳{timestamp}太旧，超过{max_age}分钟限制")

        return result

    @classmethod
    def validate_market_hours(cls, market: str, timestamp: datetime) -> ValidationResult:
        """验证市场时间是否在交易时段内"""
        result = ValidationResult()

        from ..config import Config

        hours_config = Config.MARKET_TRADING_HOURS.get(market)
        if not hours_config:
            return result  # 不做验证

        # 获取时区 - 如果没有pytz库，使用系统时区进行粗略验证
        try:
            import pytz
            if market == "US":
                tz = pytz.timezone('US/Eastern')
            elif market == "HK":
                tz = pytz.timezone('Asia/Hong_Kong')
            else:  # A-share
                tz = pytz.timezone('Asia/Shanghai')
            # 转换为市场时区
            market_time = timestamp.astimezone(tz)
        except ImportError:
            # 如果没有pytz库，使用UTC时间进行粗略检验
            market_time = timestamp.strftime('%H:%M')
            market_time = datetime.strptime(market_time, '%H:%M')
            hour = market_time.hour
            minute = market_time.minute
        hour = market_time.hour
        minute = market_time.minute

        if market == "A-share":
            morning_start = 9
            morning_end = 11
            afternoon_start = 13
            afternoon_end = 15

            def is_trading_time(h, m):
                morning_session = (h == morning_start and m >= 30) or (morning_start < h < morning_end) or (h == morning_end and m <= 30)
                afternoon_session = (h >= afternoon_start and h < afternoon_end)
                return morning_session or afternoon_session

            # 根据是否有pytz选择不同的验证方式
            if 'market_time' in locals() and isinstance(market_time, datetime):
                hour = market_time.hour
                minute = market_time.minute
                if not is_trading_time(hour, minute):
                    result.add_error(f"时间{market_time.strftime('%H:%M')}不在A股交易时间内")
            else:
                try:
                    time_str = timestamp.strftime('%H:%M')
                    hour = int(time_str[:2])
                    minute = int(time_str[3:])
                    if not is_trading_time(hour, minute):
                        result.add_error(f"时间{time_str}不在A股交易时间内（9:30-11:30, 13:00-15:00）")
                except:
                    pass  # 如果解析失败，跳过时间验证

        elif market == "US":
            # 美股：9:30-16:00
            def is_trading_time(h, m):
                return h < 9 or h >= 16 or (h == 9 and m < 30)

            if 'hour' in locals() and 'minute' in locals():
                if is_trading_time(hour, minute):
                    result.add_error(f"时间{'%02d:%02d' % (hour, minute)}不在美股交易时间内")
            else:
                try:
                    time_str = timestamp.strftime('%H:%M')
                    hour = int(time_str[:2])
                    minute = int(time_str[3:])
                    if is_trading_time(hour, minute):
                        result.add_error(f"时间{time_str}不在美股交易时间内（9:30-16:00）")
                except:
                    pass  # 如果解析失败，跳过时间验证

        elif market == "HK":
            # 港股：9:30-12:00, 13:00-16:00
            def is_trading_time(h, m):
                morning_session = (h == 9 and m >= 30) or (9 < h < 12) or (h == 12 and m == 0)
                afternoon_session = (h >= 13 and h < 16)
                return morning_session or afternoon_session

            if 'hour' in locals() and 'minute' in locals():
                if not is_trading_time(hour, minute):
                    result.add_error(f"时间{'%02d:%02d' % (hour, minute)}不在港股交易时间内")
            else:
                try:
                    time_str = timestamp.strftime('%H:%M')
                    hour = int(time_str[:2])
                    minute = int(time_str[3:])
                    if not is_trading_time(hour, minute):
                        result.add_error(f"时间{time_str}不在港股交易时间内（9:30-12:00, 13:00-16:00）")
                except:
                    pass  # 如果解析失败，跳过时间验证

        return result

# 统一验证函数
def validate_stock_symbol(symbol: str, market: Optional[str] = None) -> ValidationResult:
    """验证股票代码"""
    return StockSymbolValidator.validate(symbol, market)

def validate_price_data(data: Dict[str, Any]) -> ValidationResult:
    """验证价格数据"""
    result = PriceDataValidator.validate_price_data(data)
    result.merge(PriceDataValidator.validate_price_reasonableness(data))
    return result

def validate_time_data(timestamp: datetime, max_age: int = 60, market: Optional[str] = None) -> ValidationResult:
    """验证时间数据"""
    time_result = TimeDataValidator.validate_timestamp(timestamp, max_age, market)
    if market:
        time_result.merge(TimeDataValidator.validate_market_hours(market, timestamp))
    return time_result

def validate_market_response(data: Dict[str, Any]) -> ValidationResult:
    """验证完整的市场响应数据"""
    result = ValidationResult()

    # 基本结构验证
    required_fields = ["status", "symbol", "data"]
    for field in required_fields:
        if field not in data:
            result.add_error(f"响应数据中缺少必需字段: {field}")

    if not result:
        return result

    # 验证状态
    status = data["status"]
    if status == "success":
        # 成功响应验证
        price_result = validate_price_data(data["data"])
        result.merge(price_result)
    elif status == "error":
        # 错误响应验证（确保错误信息完整）
        error_fields = ["error_code", "error_message"]
        for field in error_fields:
            if field not in data:
                result.add_error(f"错误响应中缺少必需字段: {field}")
    else:
        result.add_error(f"不支持的响应状态: {status}")

    return result