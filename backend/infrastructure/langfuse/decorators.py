"""
Langfuse 装饰器

提供 @observable 装饰器用于非 LangChain 场景的 trace 包装。
"""

import asyncio
import logging
from functools import wraps
from typing import Callable, Optional, Any

from .client import get_langfuse_client

logger = logging.getLogger(__name__)


def observable(
    name: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
):
    """
    将函数调用包装为 Langfuse trace 的装饰器。

    用法:
        @observable(name="my_agent", user_id="user123")
        async def my_agent(query: str):
            ...

        @observable(name="sync_agent")
        def sync_process(data: dict):
            ...

    Args:
        name: trace 名称，默认使用函数名
        user_id: 用户 ID
        session_id: 会话 ID
        tags: 可选的标签列表
        metadata: 可选的元数据字典

    Returns:
        装饰后的函数，自动创建 Langfuse trace
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            langfuse = get_langfuse_client()
            if not langfuse:
                return await func(*args, **kwargs)

            trace_name = name or func.__name__

            # 解析 user_id（支持 lambda）
            resolved_user_id = user_id
            if callable(user_id):
                try:
                    resolved_user_id = user_id(args, kwargs)
                except Exception:
                    logger.warning("Failed to resolve user_id from callable")

            trace = langfuse.trace(
                name=trace_name,
                user_id=resolved_user_id,
                session_id=session_id,
                tags=tags or [],
                metadata=metadata or {},
                input=_serialize_args(args, kwargs),
            )

            try:
                result = await func(*args, **kwargs)
                trace.end(output={"result": _serialize_result(result)})
                return result
            except Exception as e:
                trace.end(level="error", status_message=str(e))
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            langfuse = get_langfuse_client()
            if not langfuse:
                return func(*args, **kwargs)

            trace_name = name or func.__name__

            # 解析 user_id（支持 lambda）
            resolved_user_id = user_id
            if callable(user_id):
                try:
                    resolved_user_id = user_id(args, kwargs)
                except Exception:
                    logger.warning("Failed to resolve user_id from callable")

            trace = langfuse.trace(
                name=trace_name,
                user_id=resolved_user_id,
                session_id=session_id,
                tags=tags or [],
                metadata=metadata or {},
                input=_serialize_args(args, kwargs),
            )

            try:
                result = func(*args, **kwargs)
                trace.end(output={"result": _serialize_result(result)})
                return result
            except Exception as e:
                trace.end(level="error", status_message=str(e))
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _serialize_args(args: tuple, kwargs: dict) -> list:
    """
    序列化函数参数用于 trace 输出。

    将非可序列化的类型转换为字符串。
    """
    serialized = []
    for arg in args:
        if isinstance(arg, (str, int, float, bool, type(None))):
            serialized.append(arg)
        elif isinstance(arg, (list, tuple, dict)):
            # 限制嵌套结构的大小
            serialized.append(_truncate_value(arg))
        else:
            serialized.append(str(arg)[:500])

    return serialized


def _serialize_result(result: Any) -> Any:
    """
    序列化函数结果用于 trace 输出。

    限制输出大小以避免数据过大。
    """
    if isinstance(result, (str, int, float, bool, type(None))):
        return result
    elif isinstance(result, (list, tuple)):
        return _truncate_value(list(result))
    elif isinstance(result, dict):
        return _truncate_value(dict(result))
    else:
        result_str = str(result)
        return result_str[:1000] if len(result_str) > 1000 else result_str


def _truncate_value(value: Any, max_length: int = 500) -> Any:
    """
    截断过大的值以避免 trace 数据过大。
    """
    if isinstance(value, str):
        return value[:max_length] + "..." if len(value) > max_length else value
    elif isinstance(value, (list, tuple)):
        return [_truncate_value(v, max_length) for v in value[:10]]  # 最多10个元素
    elif isinstance(value, dict):
        return {k: _truncate_value(v, max_length) for k, v in list(value.items())[:10]}  # 最多10个键
    return value
