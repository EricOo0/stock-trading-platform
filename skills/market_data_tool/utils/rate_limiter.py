"""
限流器模块
基于令牌桶算法的限流实现
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RateLimitExceededError(Exception):
    """限流异常"""
    def __init__(self, market: str, limit: int, remaining: int, reset_time: datetime):
        self.market = market
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time
        message = f"市场{market}的请求频率已达到上限{limit}次/小时，剩余{remaining}次，重置时间：{reset_time.strftime('%H:%M')}"
        super().__init__(message)

class TokenBucket:
    """令牌桶限流器"""

    def __init__(self, rate_per_hour: int, capacity: Optional[int] = None):
        """
        初始化令牌桶

        Args:
            rate_per_hour: 每小时令牌产生速率
            capacity: 桶容量（默认等于速率）
        """
        self.rate_per_hour = rate_per_hour
        self.tokens_per_second = rate_per_hour / 3600
        self.capacity = capacity or rate_per_hour
        self.tokens = self.capacity
        self.last_update = time.time()
        self.lock = threading.Lock()

        # 统计信息
        self.total_consumed = 0
        self.total_rejected = 0

        logger.info(f"初始化令牌桶 - 速率: {rate_per_hour}/小时, 容量: {self.capacity}")

    def consume(self, tokens: int = 1) -> bool:
        """
        消费令牌

        Args:
            tokens: 要消费的令牌数量

        Returns:
            True - 消费成功，False - 消费失败（令牌不足）
        """
        with self.lock:
            now = time.time()

            # 计算新产生的令牌
            elapsed = now - self.last_update
            new_tokens = elapsed * self.tokens_per_second
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_update = now

            # 检查令牌是否足够
            if self.tokens >= tokens:
                self.tokens -= tokens
                self.total_consumed += tokens
                return True
            else:
                self.total_rejected += tokens
                return False

    def get_status(self) -> Dict[str, Any]:
        """获取限流器状态"""
        with self.lock:
            return {
                "rate_per_hour": self.rate_per_hour,
                "capacity": self.capacity,
                "current_tokens": self.tokens,
                "total_consumed": self.total_consumed,
                "total_rejected": self.total_rejected,
                "utilization_rate": self.total_consumed / max(1, self.total_consumed + self.total_rejected)
            }

class SlidingWindowRateLimiter:
    """滑动窗口限流器（备用方案）"""

    def __init__(self, max_requests: int, window_size: int = 3600):
        """
        初始化滑动窗口限流器

        Args:
            max_requests: 窗口内最大请求数
            window_size: 窗口大小（秒）
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = []  # 存储请求时间戳
        self.lock = threading.Lock()

        logger.info(f"初始化滑动窗口限流器 - 最大请求数: {max_requests}, 窗口大小: {window_size}秒")

    def is_allowed(self) -> bool:
        """
        检查是否允许请求

        Returns:
            True - 允许，False - 拒绝
        """
        with self.lock:
            now = time.time()

            # 移除过期的请求
            cutoff_time = now - self.window_size
            self.requests = [req_time for req_time in self.requests if req_time > cutoff_time]

            # 检查当前请求数
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True

            return False

    def get_stats(self) -> Dict[str, Any]:
        """获取限流统计信息"""
        with self.lock:
            now = time.time()
            cutoff_time = now - self.window_size
            current_requests = [req_time for req_time in self.requests if req_time > cutoff_time]

            return {
                "max_requests": self.max_requests,
                "window_size": self.window_size,
                "current_requests": len(current_requests),
                "remaining_requests": self.max_requests - len(current_requests),
                "reset_time": datetime.fromtimestamp(cutoff_time + self.window_size) if current_requests else datetime.now()
            }

class RateLimiterManager:
    """限流器管理器"""

    def __init__(self):
        self.limiters: Dict[str, TokenBucket] = {}
        self.lock = threading.Lock()

        # 初始化各市场的限流器
        # 初始化各个市场的限流器
        from ..config import Config

        self.limiters["A-share"] = TokenBucket(Config.RATE_LIMIT_A_SHARE, 10)
        self.limiters["US"] = TokenBucket(Config.RATE_LIMIT_US, 5)
        self.limiters["HK"] = TokenBucket(Config.RATE_LIMIT_HK, 5)

        logger.info("限流器管理器已初始化")

    def check_and_consume(self, market: str, tokens: int = 1) -> bool:
        """
        检查并消费指定市场的请求配额

        Args:
            market: 市场类型
            tokens: 消费量

        Returns:
            True - 允许请求，False - 限流
        """
        if market not in self.limiters:
            logger.warning(f"未找到市场{market}的限流器，使用默认值")
            return True

        limiter = self.limiters[market]
        allowed = limiter.consume(tokens)

        if allowed:
            logger.debug(f"市场{market}消费{tokens}个令牌成功")
        else:
            stats = limiter.get_status()
            logger.warning(f"市场{market}限流 - 剩余{stats['current_tokens']}令牌")

        return allowed

    def get_rate_limit_info(self, market: str) -> Dict[str, Any]:
        """
        获取指定市场的限流信息

        Args:
            market: 市场类型

        Returns:
            限流信息字典
        """
        if market not in self.limiters:
            return {
                "market": market,
                "exists": False,
                "suggestion": "市场类型不支持"
            }

        limiter = self.limiters[market]
        status = limiter.get_status()

        return {
            "market": market,
            "exists": True,
            "rate_limit": status["rate_per_hour"],
            "capacity": status["capacity"],
            "remaining_tokens": int(status["current_tokens"]),
            "utilization_rate": f"{status['utilization_rate']:.1%}",
            "time_to_reset": self._calculate_reset_time(market),
            "suggestion": "正常配额充足" if status["current_tokens"] > 1 else "配额紧张，建议稍后再试"
        }

    def get_all_rate_limits(self) -> Dict[str, Dict[str, Any]]:
        """获取所有市场的限流信息"""
        result = {}
        for market in self.limiters:
            result[market] = self.get_rate_limit_info(market)
        return result

    def _calculate_reset_time(self, market: str) -> str:
        """计算配额重置时间"""
        limiter = self.limiters[market]
        status = limiter.get_status()

        # 如果令牌桶为空，计算重新填满的时间
        if status["current_tokens"] <= 0:
            seconds_needed = 3600 / status["rate_per_hour"]
            reset_time = datetime.now() + timedelta(seconds=seconds_needed)
            return reset_time.strftime("%H:%M")

        return "可用"

    def reset_rate_limit(self, market: str):
        """重置指定市场的限流器"""
        if market in self.limiters:
            with self.lock:
                # 重新初始化限流器
                old_limiter = self.limiters[market]
                self.limiters[market] = TokenBucket(
                    old_limiter.rate_per_hour,
                    old_limiter.capacity
                )
                logger.info(f"市场{market}的限流器已重置")

    def get_global_stats(self) -> Dict[str, Any]:
        """获取全局统计信息"""
        total_consumed = 0
        total_rejected = 0
        market_stats = {}

        for market, limiter in self.limiters.items():
            status = limiter.get_status()
            total_consumed += status["total_consumed"]
            total_rejected += status["total_rejected"]
            market_stats[market] = {
                "consumed": status["total_consumed"],
                "rejected": status["total_rejected"],
                "utilization": f"{status['utilization_rate']:.1%}"
            }

        return {
            "total_consumed": total_consumed,
            "total_rejected": total_rejected,
            "overall_utilization": f"{total_consumed / max(1, total_consumed + total_rejected):.1%}",
            "market_breakdown": market_stats,
            "timestamp": datetime.now().isoformat()
        }

# 全局限流器实例
rate_limiter = RateLimiterManager()