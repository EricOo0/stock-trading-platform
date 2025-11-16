"""
数据源基类定义
定义通用的数据源接口和基础功能
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class DataSourceError(Exception):
    """数据源异常基类"""

    def __init__(self, message: str, provider: str, error_code: str = "API_ERROR"):
        self.message = message
        self.provider = provider
        self.error_code = error_code
        super().__init__(message)

class DataSourceTimeout(DataSourceError):
    """数据源超时异常"""

    def __init__(self, provider: str, timeout: int):
        super().__init__(
            message=f"数据源{provider}请求超时({timeout}秒)",
            provider=provider,
            error_code="TIMEOUT"
        )

class SymbolNotFoundError(DataSourceError):
    """股票代码不存在异常"""

    def __init__(self, symbol: str, provider: str):
        super().__init__(
            message=f"股票代码{symbol}在数据源{provider}中不存在",
            provider=provider,
            error_code="SYMBOL_NOT_FOUND"
        )

class BaseDataSource(ABC):
    """数据源基类"""

    def __init__(self, name: str, timeout: int = 10):
        """
        初始化数据源

        Args:
            name: 数据源名称
            timeout: 请求超时时间（秒）
        """
        self.name = name
        self.timeout = timeout
        self.logger = logging.getLogger(f"datasource.{name}")

    @abstractmethod
    def get_stock_quote(self, symbol: str, market: str) -> Dict[str, Any]:
        """
        获取股票行情数据

        Args:
            symbol: 股票代码
            market: 市场类型(A-share, US, HK)

        Returns:
            股票行情数据字典

        Raises:
            DataSourceError: 数据源异常
        """
        pass

    @abstractmethod
    def validate_symbol(self, symbol: str, market: str) -> bool:
        """
        验证股票代码是否有效

        Args:
            symbol: 股票代码
            market: 市场类型

        Returns:
            True如果有效，False如果无效
        """
        pass

    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """
        批量获取股票行情数据

        Args:
            symbols: 股票代码列表

        Returns:
            股票字典，键为股票代码，值为行情数据
        """
        results = {}
        failed_symbols = []

        for symbol in symbols:
            try:
                # 检测市场类型
                market = self._detect_market(symbol)
                data = self.get_stock_quote(symbol, market)
                results[symbol] = {
                    "status": "success",
                    "data": data
                }
            except Exception as e:
                self.logger.error(f"获取{symbol}数据失败: {e}")
                results[symbol] = {
                    "status": "error",
                    "error_message": str(e)
                }
                failed_symbols.append(symbol)

        # 统计结果
        success_count = len(results) - len(failed_symbols)

        return {
            "status": "success" if len(failed_symbols) == 0 else "partial",
            "requested_symbols": symbols,
            "successful_symbols": [s for s in symbols if s not in failed_symbols],
            "failed_symbols": failed_symbols,
            "data": results,
            "success_rate": success_count / len(symbols) if symbols else 0,
            "timestamp": datetime.now().isoformat()
        }

    def _detect_market(self, symbol: str) -> str:
        """
        根据股票代码自动检测市场类型

        Args:
            symbol: 股票代码

        Returns:
            市场类型
        """
        import re

        # A股：6位数字，指定前缀开头
        if re.match(r'^(000|002|300|600|601|603)\d{3}$', symbol):
            return "A-share"

        # 美股：1-5位字母
        if re.match(r'^[A-Z]{1,5}$', symbol.upper()):
            return "US"

        # 港股：5位数字，以0开头
        if re.match(r'^0\d{4}$', symbol):
            return "HK"

        # 默认返回A股
        return "A-share"

    def _create_error_response(self, symbol: str, error: Exception) -> Dict[str, Any]:
        """
        创建错误响应

        Args:
            symbol: 股票代码
            error: 异常对象

        Returns:
            错误响应字典
        """
        error_code = "API_ERROR"
        error_message = str(error)

        if isinstance(error, DataSourceTimeout):
            error_code = "TIMEOUT"
            error_message = f"数据源{self.name}请求超时"
        elif isinstance(error, SymbolNotFoundError):
            error_code = "SYMBOL_NOT_FOUND"
            error_message = f"股票代码{symbol}不存在"

        return {
            "status": "error",
            "symbol": symbol,
            "error_code": error_code,
            "error_message": error_message,
            "data_source": self.name,
            "timestamp": datetime.now().isoformat()
        }