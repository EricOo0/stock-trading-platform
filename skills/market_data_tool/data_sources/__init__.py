"""
数据源模块初始化文件
提供金融市场数据获取的基本接口和实现
"""

from .base import (
    BaseDataSource,
    DataSourceError,
    DataSourceTimeout,
    SymbolNotFoundError
)

# Optional: 具体的实现类会在后续按需导入
# from .yahoo_finance import YahooFinanceDataSource
# from .sina_finance import SinaFinanceDataSource

# 数据源导出列表
__all__ = [
    # 基础类
    "BaseDataSource",
    "DataSourceError",
    "DataSourceTimeout",
    "SymbolNotFoundError",
]