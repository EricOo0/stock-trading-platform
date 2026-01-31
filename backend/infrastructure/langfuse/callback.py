"""
Langfuse Callback Handler

Provides LangChain CallbackHandler for Langfuse observability integration.

在 Langfuse v3 中，user_id 和 session_id 需要通过 metadata 传递：
- metadata["langfuse_user_id"] - 用户 ID
- metadata["langfuse_session_id"] - 会话 ID
- metadata["langfuse_tags"] - 标签列表
"""

import logging
from typing import Optional, Dict, Any

from .client import langfuse_enabled

logger = logging.getLogger(__name__)


def create_langfuse_callback(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
):
    """
    创建 Langfuse CallbackHandler 实例。

    如果 Langfuse 未配置，返回 None（优雅降级）。

    Args:
        user_id: 用户 ID，用于追踪
        session_id: 会话 ID，用于分组
        tags: 可选的标签列表
        metadata: 额外的元数据

    Returns:
        langfuse.langchain.CallbackHandler 实例或 None

    用法:
        # 1. 创建回调
        callback = create_langfuse_callback(user_id="user123", session_id="session456")

        # 2. 与现有回调一起使用
        callbacks = [
            ResearchAgentCallback(),
            callback,  # 如果未配置则为 None
        ]
        callbacks = [cb for cb in callbacks if cb is not None]

        # 3. 在 agent 调用处通过 metadata 传递 user_id/session_id
        await graph.ainvoke(
            inputs,
            config={
                "callbacks": callbacks,
                "metadata": {
                    "langfuse_user_id": "user123",
                    "langfuse_session_id": "session456",
                }
            }
        )
    """
    if not langfuse_enabled():
        logger.debug("Langfuse not enabled, callback disabled")
        return None

    from langfuse.langchain import CallbackHandler

    # Langfuse v3 中，user_id/session_id 需要通过 metadata 传递
    # 不在 CallbackHandler 初始化时传递，而是在 agent 调用处传递
    return CallbackHandler()


def build_langfuse_metadata(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    构建 Langfuse metadata 字典。

    在 Langfuse v3 中，user_id、session_id、tags 需要通过特定的 metadata 键传递。

    Args:
        user_id: 用户 ID
        session_id: 会话 ID
        tags: 标签列表
        metadata: 额外的元数据

    Returns:
        包含 Langfuse 特定键的元数据字典
    """
    result: Dict[str, Any] = {}

    if user_id is not None:
        result["langfuse_user_id"] = user_id

    if session_id is not None:
        result["langfuse_session_id"] = session_id

    if tags is not None and len(tags) > 0:
        result["langfuse_tags"] = tags

    if metadata is not None:
        result.update(metadata)

    return result
