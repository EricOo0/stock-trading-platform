"""
Langfuse Callback Handler (v3)

使用 Langfuse v3 的 langchain.CallbackHandler 进行 LangChain 集成。

v3 变化：
- 导入路径：from langfuse.langchain import CallbackHandler
- CallbackHandler 不再接受 user_id/session_id 参数，需要通过 metadata 传递
- 首次导入时会自动创建全局客户端，因此需要先设置环境变量
"""

import logging
import os
from typing import Optional, Dict, Any

from .client import langfuse_enabled, ensure_env_vars

logger = logging.getLogger(__name__)

# 标记 CallbackHandler 是否可用
_CALLBACK_HANDLER_AVAILABLE = False
_CallbackHandler = None


def create_langfuse_callback(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
):
    """
    创建 Langfuse CallbackHandler 实例（v3 API）。

    在 v3 中，CallbackHandler 不再接受 user_id/session_id 等参数。
    这些参数需要通过 config["metadata"] 在 invoke 时传递。

    如果 Langfuse 未配置或 CallbackHandler 不可用，返回 None（优雅降级）。

    Args:
        user_id: 用户 ID（v3 中仅用于日志记录，实际通过 metadata 传递）
        session_id: 会话 ID（v3 中仅用于日志记录，实际通过 metadata 传递）
        tags: 可选的标签列表（v3 中通过 metadata 传递）
        metadata: 额外的元数据

    Returns:
        langfuse.langchain.CallbackHandler 实例或 None
    """
    if not langfuse_enabled():
        logger.debug("Langfuse not enabled, callback disabled")
        return None

    # 在导入前先确保环境变量已设置（避免模块级别导入触发全局客户端创建）
    ensure_env_vars()

    # 确保 env vars 设置后再导入 CallbackHandler
    try:
        from langfuse.langchain import CallbackHandler as _CallbackHandler
        _CALLBACK_HANDLER_AVAILABLE = True
        logger.debug("Langfuse v3 CallbackHandler imported successfully")
    except ImportError as e:
        logger.warning(f"Langfuse CallbackHandler not available: {e}")
        logger.warning("Install with: pip install 'langfuse>=3.0.0'")
        return None

    if not _CALLBACK_HANDLER_AVAILABLE or _CallbackHandler is None:
        logger.debug("Langfuse CallbackHandler not available, skipping")
        return None

    # v3: CallbackHandler 不接受参数，返回空实例
    logger.debug(f"Creating Langfuse CallbackHandler (v3)")
    return _CallbackHandler()


def build_langfuse_metadata(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    构建 Langfuse metadata 字典（v3 API）。

    在 v3 中，user_id、session_id、tags 需要通过 metadata 传递，
    使用特定的键名前缀 langfuse_*。

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
