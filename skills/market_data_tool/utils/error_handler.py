"""
错误处理模块
统一管理错误类型和处理逻辑
"""

from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)

class MarketDataToolError(Exception):
    """市场数据工具自定义异常基类"""

    def __init__(self, code: str, message: str, suggestion: str = "",
                 context: Optional[Dict[str, Any]] = None):
        """
        初始化异常

        Args:
            code: 错误代码
            message: 错误消息
            suggestion: 用户建议
            context: 错误上下文
        """
        self.code = code
        self.message = message
        self.suggestion = suggestion
        self.context = context or {}
        super().__init__(message)

class SymbolValidationError(MarketDataToolError):
    """股票代码验证错误"""
    def __init__(self, symbol: str, details: str = ""):
        super().__init__(
            code="INVALID_SYMBOL",
            message=f"股票代码{symbol}格式错误或无效",
            suggestion="请检查股票代码格式：A股6位数字，美股1-5位字母，港股5位数字以0开头",
            context={"symbol": symbol, "details": details}
        )

class RateLimitExceededError(MarketDataToolError):
    """限流错误"""
    def __init__(self, market: str, limit: int, remaining: int):
        super().__init__(
            code="RATE_LIMITED",
            message=f"市场{market}的请求频率已达到上限{limit}次/小时",
            suggestion="请等待1小时后重试，或查询其他市场的股票",
            context={"market": market, "rate_limit": limit, "remaining": remaining}
        )

class DataSourceError(MarketDataToolError):
    """数据源错误"""
    def __init__(self, provider: str, error: Exception):
        super().__init__(
            code="API_ERROR",
            message=f"数据源{provider}不可用或返回错误",
            suggestion="系统将自动尝试备用数据源，请稍后重试",
            context={"provider": provider, "original_error": str(error)}
        )

class ServiceUnavailableError(MarketDataToolError):
    """服务不可用错误"""
    def __init__(self, services: List[str]):
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=f"所有数据源均不可用",
            suggestion="请稍后重试，或检查网络连接",
            context={"failed_services": services, "service_list": services}
        )

class ValidationError(MarketDataToolError):
    """数据验证错误"""
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            code="VALIDATION_ERROR",
            message=f"字段{field}的值{value}验证失败",
            suggestion="请检查数据格式和内容",
            context={"field": field, "value": value, "reason": reason}
        )

def create_error_response(
    symbol: str,
    error_code: str,
    error_message: str,
    suggestion: str = "",
    context: Optional[Dict[str, Any]] = None,
    data_source: str = "unknown"
) -> Dict[str, Any]:
    """
    创建标准化的错误响应

    Args:
        symbol: 股票代码
        error_code: 错误代码
        error_message: 错误消息
        suggestion: 用户建议
        context: 错误上下文
        data_source: 数据源名称

    Returns:
        标准化的错误响应字典
    """
    return {
        "status": "error",
        "symbol": symbol,
        "error_code": error_code,
        "error_message": error_message,
        "suggestion": suggestion,
        "context": context or {},
        "data_source": data_source,
        "timestamp": datetime.now().isoformat()
    }

def create_success_response(
    symbol: str,
    data: Dict[str, Any],
    data_source: str,
    cache_hit: bool = False,
    response_time_ms: float = None
) -> Dict[str, Any]:
    """
    创建标准化的成功响应

    Args:
        symbol: 股票代码
        data: 股票数据
        data_source: 数据源名称
        cache_hit: 是否缓存命中
        response_time_ms: 响应时间（毫秒）

    Returns:
        标准化的成功响应字典
    """
    return {
        "status": "success",
        "symbol": symbol,
        "data": data,
        "data_source": data_source,
        "cache_hit": cache_hit,
        "response_time_ms": response_time_ms,
        "timestamp": datetime.now().isoformat()
    }

def create_partial_response(
    results: List[Dict[str, Any]],
    data_source: str,
    total_time_ms: float
) -> Dict[str, Any]:
    """
    创建批量查询的部分成功响应

    Args:
        results: 查询结果列表
        data_source: 数据源名称
        total_time_ms: 总响应时间

    Returns:
        部分成功的批处理响应字典
    """
    successful_count = sum(1 for r in results if r.get("status") == "success")
    failed_count = len(results) - successful_count

    return {
        "status": "partial",
        "count": len(results),
        "successful_count": successful_count,
        "failed_count": failed_count,
        "success_rate": successful_count / len(results) if results else 0,
        "results": results,
        "data_source": data_source,
        "total_response_time_ms": total_time_ms,
        "timestamp": datetime.now().isoformat()
    }

class ErrorHandler:
    """错误处理器类"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_stats = {
            "total_errors": 0,
            "error_counts": {}
        }

    def handle_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理异常并返回标准化的错误响应

        Args:
            exception: 异常对象
            context: 错误上下文

        Returns:
            错误响应字典
        """
        context = context or {}  # Ensure context is always a dict
        self.error_stats["total_errors"] += 1

        # 记录错误统计
        error_type = exception.__class__.__name__
        self.error_stats["error_counts"][error_type] = self.error_stats["error_counts"].get(error_type, 0) + 1

        # 记录详细错误信息
        error_context = {
            "exception_type": error_type,
            "exception_message": str(exception),
            "stack_trace": traceback.format_exc(),
            "context": context
        }
        # Merge MarketDataToolError context if available
        if isinstance(exception, MarketDataToolError) and exception.context:
            error_context.update(exception.context)
        self.logger.error(f"错误处理 - {error_type}: {exception}", extra=error_context)

        # 针对不同异常类型创建相应响应
        if isinstance(exception, MarketDataToolError):
            return create_error_response(
                symbol=context.get("symbol", "unknown"),
                error_code=exception.code,
                error_message=exception.message,
                suggestion=exception.suggestion,
                context=exception.context,
                data_source=context.get("provider", "unknown")
            )
        elif isinstance(exception, ValueError):
            return create_error_response(
                symbol=context.get("symbol", "unknown"),
                error_code="INVALID_INPUT",
                error_message=f"输入参数错误: {str(exception)}",
                suggestion="请检查输入参数格式",
                context=context
            )
        else:
            # 未知异常 - include the original context in the response
            return create_error_response(
                symbol=context.get("symbol", "unknown"),
                error_code="INTERNAL_ERROR",
                error_message="系统内部错误，请稍后重试",
                suggestion="如果问题持续，请联系技术支持",
                context={**error_context, **context}  # Merge contexts
            )

    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return {
            "total_errors": self.error_stats["total_errors"],
            "error_breakdown": self.error_stats["error_counts"],
            "timestamp": datetime.now().isoformat()
        }

def error_boundary(func: Callable) -> Callable:
    """
    错误边界装饰器

    Args:
        func: 要装饰的函数

    Returns:
        包装后的函数
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler = ErrorHandler()

            # Build context with function info and extracted arguments
            context = {"function": func.__name__}

            # Handle both positional and keyword arguments for context extraction
            import inspect
            try:
                # Get parameter names from function signature
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())

                # Map positional args to parameter names
                for i, arg_value in enumerate(args):
                    if i < len(param_names):
                        context[param_names[i]] = arg_value

                # Add keyword args
                context.update(kwargs)
            except Exception:
                # Fallback: just store as strings if signature inspection fails
                context["args"] = str(args)
                context["kwargs"] = str(kwargs)

            return error_handler.handle_error(e, context)
    return wrapper