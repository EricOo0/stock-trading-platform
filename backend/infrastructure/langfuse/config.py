"""
Langfuse 配置管理

处理配置加载，支持从环境变量和 ConfigLoader 读取。
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LangfuseConfig:
    """
    Langfuse 配置类，支持多种配置来源。

    优先级：
    1. 环境变量 (LANGFUSE_*)
    2. ConfigLoader 集成
    """

    def __init__(self, public_key: Optional[str] = None, secret_key: Optional[str] = None):
        # 直接初始化（用于测试）
        self._public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        self._secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self._base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
        self._release = os.getenv("LANGFUSE_RELEASE", "development")

        # 尝试从 ConfigLoader 加载
        if not self._public_key or not self._secret_key:
            self._load_from_config_loader()

        self._enabled = bool(self._public_key and self._secret_key)

    def _load_from_config_loader(self):
        """尝试从 ConfigLoader 加载 langfuse 配置。"""
        try:
            from backend.infrastructure.config.loader import ConfigLoader
            config = ConfigLoader.load_config()
            langfuse_config = config.get("langfuse", {})

            if not self._public_key:
                self._public_key = langfuse_config.get("public_key")
            if not self._secret_key:
                self._secret_key = langfuse_config.get("secret_key")
            if self._base_url == "https://cloud.langfuse.com":
                custom_url = langfuse_config.get("base_url")
                if custom_url:
                    self._base_url = custom_url
            if self._release == "development":
                custom_release = langfuse_config.get("release")
                if custom_release:
                    self._release = custom_release

            if self._public_key or self._secret_key:
                logger.info("Langfuse config loaded from ConfigLoader")
        except Exception as e:
            logger.debug(f"Could not load langfuse from ConfigLoader: {e}")

    @property
    def public_key(self) -> Optional[str]:
        """获取 Langfuse 公钥。"""
        return self._public_key

    @property
    def secret_key(self) -> Optional[str]:
        """获取 Langfuse 密钥。"""
        return self._secret_key

    @property
    def base_url(self) -> str:
        """获取 Langfuse 主机 URL。"""
        return self._base_url

    @property
    def release(self) -> str:
        """获取 Langfuse 发布环境。"""
        return self._release

    @property
    def enabled(self) -> bool:
        """检查 Langfuse 是否已配置并启用。"""
        return self._enabled

    @property
    def api_keys(self) -> Optional[tuple]:
        """
        返回 (public_key, secret_key) 元组或 None。

        Returns:
            Tuple[str, str] 或 None: API keys（如果已配置），None（否则）。
        """
        if not self._enabled:
            return None
        return (self._public_key, self._secret_key)


# 全局配置单例
_config = LangfuseConfig()


def get_langfuse_config() -> LangfuseConfig:
    """获取全局 Langfuse 配置单例。"""
    return _config


def reload_config():
    """重新加载 Langfuse 配置（用于测试）。"""
    global _config
    _config = LangfuseConfig()
    return _config
