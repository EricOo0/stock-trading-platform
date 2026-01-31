"""
Langfuse 客户端单例 (v3)

管理 Langfuse SDK v3 客户端的初始化和单例访问。

v3 变化：
- 推荐使用 get_client() 获取全局客户端
- 支持环境变量自动配置
- 仍然支持 Langfuse() 构造函数创建新实例
"""

import logging
import os
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


def ensure_env_vars():
    """
    确保 Langfuse 环境变量已设置（v3 推荐方式）。

    v3 优先使用环境变量进行配置。
    这个函数需要在导入 CallbackHandler 之前调用。
    """
    config = get_langfuse_config()

    if config.public_key and not os.getenv("LANGFUSE_PUBLIC_KEY"):
        os.environ["LANGFUSE_PUBLIC_KEY"] = config.public_key
        logger.debug("Set LANGFUSE_PUBLIC_KEY from config")

    if config.secret_key and not os.getenv("LANGFUSE_SECRET_KEY"):
        os.environ["LANGFUSE_SECRET_KEY"] = config.secret_key
        logger.debug("Set LANGFUSE_SECRET_KEY from config")

    if config.base_url and config.base_url != "https://cloud.langfuse.com" and not os.getenv("LANGFUSE_HOST"):
        os.environ["LANGFUSE_HOST"] = config.base_url
        logger.debug("Set LANGFUSE_HOST from config")


def get_langfuse_client():
    """
    获取 Langfuse 客户端单例（v3 API）。

    如果 Langfuse 未配置，返回 None（优雅降级）。
    客户端在首次调用时初始化。

    v3 优先使用环境变量配置，但也可以通过构造函数传参。

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
            # v3: 优先使用环境变量
            ensure_env_vars()

            # v3: 使用 get_client() 获取全局客户端（推荐）
            # 或者使用 Langfuse() 创建新实例
            from langfuse import Langfuse, get_client

            # 尝试使用环境变量配置
            if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
                # 使用全局客户端（自动读取环境变量）
                _langfuse_client = get_client()
                logger.info(
                    f"Langfuse v3 client initialized via environment variables "
                    f"(release={config.release})"
                )
            else:
                # 使用构造函数传参
                _langfuse_client = Langfuse(
                    public_key=config.public_key,
                    secret_key=config.secret_key,
                    host=config.base_url,
                    release=config.release,
                )
                logger.info(
                    f"Langfuse v3 client initialized via constructor "
                    f"(release={config.release}, host={config.base_url})"
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
