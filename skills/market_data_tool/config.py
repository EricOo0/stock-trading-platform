"""
配置文件模块
管理市场数据工具的所有配置项
"""

import os
from typing import Dict, Any
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional, use defaults if not available
    pass

class Config:
    """配置管理类"""

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # 缓存配置
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 缓存时间（秒）

    # 限流配置（每小时请求次数）
    RATE_LIMIT_A_SHARE = int(os.getenv("RATE_LIMIT_A_SHARE", "120"))
    RATE_LIMIT_US = int(os.getenv("RATE_LIMIT_US", "60"))
    RATE_LIMIT_HK = int(os.getenv("RATE_LIMIT_HK", "60"))

    # 熔断器配置
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "300"))  # 秒

    # API配置
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))  # API超时时间（秒）
    API_RETRY_COUNT = int(os.getenv("API_RETRY_COUNT", "3"))

    # 数据源权重
    PRIMARY_DATA_SOURCE = "yahoo"
    BACKUP_DATA_SOURCE = "sina"

    # 批量查询配置
    BATCH_MAX_SYMBOLS = 10
    BATCH_TIMEOUT = int(os.getenv("BATCH_TIMEOUT", "30"))  # 批处理超时时间（秒）

    # 市场配置
    MARKET_TRADING_HOURS = {
        "A-share": {
            "morning_start": "09:30",
            "morning_end": "11:30",
            "afternoon_start": "13:00",
            "afternoon_end": "15:00"
        },
        "US": {
            "start": "09:30",
            "end": "16:00"
        },
        "HK": {
            "morning_start": "09:30",
            "morning_end": "12:00",
            "afternoon_start": "13:00",
            "afternoon_end": "16:00"
        }
    }

    # A股股票代码前缀验证
    A_SHARE_PREFIXES = ["000", "001", "002", "300", "600", "601", "603"]

    @classmethod
    def get_rate_limit_config(cls, market: str) -> int:
        """获取指定市场的限流配置"""
        rate_limits = {
            "A-share": cls.RATE_LIMIT_A_SHARE,
            "US": cls.RATE_LIMIT_US,
            "HK": cls.RATE_LIMIT_HK
        }
        return rate_limits.get(market, cls.RATE_LIMIT_A_SHARE)

    def validate_symbol_format(self, symbol: str, market: str) -> bool:
        """验证股票代码格式"""
        import re

        if market == "A-share":
            # A股：6位数字，指定前缀开头
            if re.match(rf'^({"|".join(cls.A_SHARE_PREFIXES)})\d{{3}}$', symbol):
                return True
        elif market == "US":
            # 美股：1-5位字母
            if re.match(r'^[A-Z]{1,5}$', symbol.upper()):
                return True
        elif market == "HK":
            # 港股：5位数字，以0开头
            if re.match(r'^0\d{4}$', symbol):
                return True

        return False