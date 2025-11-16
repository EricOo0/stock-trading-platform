"""
数据模型定义
定义股票、指数和响应数据结构
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator

class StockData(BaseModel):
    """股票行情数据模型"""

    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    current_price: float = Field(..., description="当前价格", ge=0)
    open_price: float = Field(..., description="开盘价", ge=0)
    high_price: float = Field(..., description="最高价", ge=0)
    low_price: float = Field(..., description="最低价", ge=0)
    previous_close: float = Field(..., description="昨收价", ge=0)
    change_amount: float = Field(..., description="涨跌额")
    change_percent: float = Field(..., description="涨跌幅百分比")
    volume: int = Field(..., description="成交量", ge=0)
    turnover: float = Field(..., description="成交额", ge=0)
    timestamp: datetime = Field(..., description="数据时间戳")
    market: str = Field(..., description="市场分类")
    currency: str = Field(..., description="货币")
    status: str = Field(default="trading", description="交易状态")

    @validator('high_price', 'low_price', 'current_price')
    def validate_price_relationships(cls, v, values):
        """验证价格之间的关系"""
        if 'low_price' in values and 'high_price' in values:
            low = values.get('low_price')
            high = values.get('high_price')
            if low > high:
                raise ValueError("最低价不能高于最高价")
            if 'current_price' in values:
                current = values.get('current_price')
                if not (low <= current <= high):
                    raise ValueError("当前价格必须在最高价和最低价范围内")
        return v

    @validator('change_percent')
    def validate_change_percent(cls, v):
        """验证涨跌幅范围"""
        if abs(v) > 20:  # A股涨跌停限制约为20%
            raise ValueError(f"涨跌幅{v}%超出正常范围")
        return v

    class Config:
        schema_extra = {
            "example": {
                "symbol": "000001",
                "name": "平安银行",
                "current_price": 12.45,
                "open_price": 12.20,
                "high_price": 12.50,
                "low_price": 12.15,
                "previous_close": 12.16,
                "change_amount": 0.29,
                "change_percent": 2.38,
                "volume": 1234567,
                "turnover": 15370000,
                "timestamp": "2025-11-09T15:30:00",
                "market": "A-share",
                "currency": "CNY",
                "status": "trading"
            }
        }

class IndexData(BaseModel):
    """市场指数数据模型"""

    symbol: str = Field(..., description="指数代码")
    name: str = Field(..., description="指数名称")
    current_value: float = Field(..., description="当前点位", ge=0)
    open_value: float = Field(..., description="开盘点位", ge=0)
    high_value: float = Field(..., description="最高点位", ge=0)
    low_value: float = Field(..., description="最低点位", ge=0)
    previous_close: float = Field(..., description="昨收点位", ge=0)
    change_amount: float = Field(..., description="涨跌点位")
    change_percent: float = Field(..., description="涨跌幅百分比")
    timestamp: datetime = Field(..., description="数据时间戳")
    market: str = Field(..., description="关联市场")

    @validator('change_percent')
    def validate_index_change_percent(cls, v):
        """验证指数涨跌幅范围"""
        if abs(v) > 10:  # 指数涨跌停限制约为10%
            raise ValueError(f"指数涨跌幅{v}%超出正常范围")
        return v

class ErrorInfo(BaseModel):
    """错误信息模型"""

    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    suggestion: str = Field(..., description="用户建议")
    context: Dict[str, Any] = Field(default_factory=dict, description="错误上下文信息")
    provider: str = Field(..., description="出错的提供商")
    timestamp: datetime = Field(..., description="错误时间戳")

class MarketResponse(BaseModel):
    """市场数据响应模型"""

    status: str = Field(..., description="响应状态")
    symbol: str = Field(..., description="请求的股票代码")
    data: Optional[Dict[str, Any]] = Field(None, description="主要数据内容")
    error_code: Optional[str] = Field(None, description="错误代码")
    error_message: Optional[str] = Field(None, description="错误消息")
    suggestion: Optional[str] = Field(None, description="用户建议")
    timestamp: datetime = Field(..., description="响应时间戳")
    data_source: str = Field(..., description="数据源")
    cache_hit: bool = Field(default=False, description="是否缓存命中")
    response_time_ms: float = Field(..., description="响应时间")

    @validator('status')
    def validate_status(cls, v):
        """验证响应状态"""
        allowed_statuses = ["success", "error", "partial"]
        if v not in allowed_statuses:
            raise ValueError(f"状态必须是{allowed_statuses}之一")
        return v

class BatchMarketResponse(BaseModel):
    """批量市场数据响应模型"""

    status: str = Field(..., description="批量响应状态")
    count: int = Field(..., description="查询数量")
    symbols: List[str] = Field(..., description="查询的股票代码列表")
    results: List[MarketResponse] = Field(..., description="个股查询结果列表")
    timestamp: datetime = Field(..., description="响应时间戳")
    total_response_time_ms: float = Field(..., description="总响应时间")

class RateLimit(BaseModel):
    """限流信息模型"""

    market: str = Field(..., description="市场类型")
    requests_per_hour: int = Field(..., description="每小时最大请求数")
    remaining_requests: int = Field(..., description="剩余请求数")
    window_start: datetime = Field(..., description="时间窗口开始")
    window_end: datetime = Field(..., description="时间窗口结束")
    reset_time: datetime = Field(..., description="限制重置时间")