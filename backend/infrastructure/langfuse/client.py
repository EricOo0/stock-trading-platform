"""
Langfuse 客户端单例

管理 Langfuse SDK 客户端的初始化和单例访问。
"""

import logging
from typing import Optional

from .config import get_langfuse_config

logger = logging.getLogger(__name__)

# 全局 Langfuse 客户端实例
_langfuse_client: Optional["Langfuse"] = None


def langfuse_enabled() -> bool:
    """
    检查 Langfuse 是否已配置并启用。

    Returns:
        bool: True if Langfuse is enabled, False otherwise.
    """
    config = get_langfuse_config()
    return config.enabled


def get_langfuse_client():
    """
    获取 Langfuse 客户端单例。

    如果 Langfuse 未配置，返回 None（优雅降级）。
    客户端在首次调用时初始化。

    Returns:
        langfuse.Langfuse: Langfuse client instance, or None if disabled.
    """
    global _langfuse_client

    config = get_langfuse_config()

    if not config.enabled:
        logger.debug("Langfuse is not configured, skipping...")
        return None

    if _langfuse_client is None:
        try:
            from langfuse import Langfuse

            _langfuse_client = Langfuse(
                public_key=config.public_key,
                secret_key=config.secret_key,
                host=config.base_url,
                release=config.release,
            )
            logger.info(
                f"Langfuse client initialized (release={config.release}, "
                f"host={config.base_url})"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse client: {e}")
            _langfuse_client = None
            return None

    return _langfuse_client


def reset_client():
    """
    重置 Langfuse 客户端单例。

    用于测试或配置变更时重新初始化。
    """
    global _langfuse_client
    _langfuse_client = None
