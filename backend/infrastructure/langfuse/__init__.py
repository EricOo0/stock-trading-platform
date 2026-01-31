"""
Langfuse 可观测性基础设施

这个模块提供统一的 Langfuse 集成接口，用于所有 agent 的可观测性追踪。

使用方法:
    from backend.infrastructure.langfuse import (
        create_langfuse_callback,
        build_langfuse_metadata,
        observable,
    )
"""

from .client import get_langfuse_client, langfuse_enabled
from .callback import create_langfuse_callback, build_langfuse_metadata
from .decorators import observable

__all__ = [
    "create_langfuse_callback",
    "build_langfuse_metadata",
    "observable",
    "get_langfuse_client",
    "langfuse_enabled",
]
