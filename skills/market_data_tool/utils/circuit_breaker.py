"""
熔断器模块
实现熔断器模式，防止级联故障
"""

import time
import threading
from enum import Enum
from typing import Optional, Callable, Any, Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"         # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态

class CircuitBreakerError(Exception):
    """熔断器异常"""
    def __init__(self, message: str, state: CircuitState, provider: str):
        self.state = state
        self.provider = provider
        super().__init__(message)

class CircuitBreaker:
    """熔断器实现"""

    def __init__(self, name: str, failure_threshold: int = 5,
                 recovery_timeout: int = 300, success_threshold: int = 3):
        """
        初始化熔断器

        Args:
            name: 熔断器名称
            failure_threshold: 失败次数阈值
            recovery_timeout: 恢复超时时间（秒）
            success_threshold: 半开状态下的成功次数阈值
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        # 状态变量
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()

        # 统计信息
        self.total_calls = 0
        self.failed_calls = 0
        self.successful_calls = 0

        # 锁
        self.lock = threading.Lock()

        logger.info(f"熔断器{name}已初始化 - 失败阈值: {failure_threshold}, 恢复超时: {recovery_timeout}秒")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        调用函数并应用熔断器逻辑

        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值

        Raises:
            CircuitBreakerError: 熔断器异常
            Exception: 原始异常（在熔断状态下会被包装）
        """
        with self.lock:
            self.total_calls += 1

        # 检查当前状态
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                # 尝试进入半开状态
                with self.lock:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    self.last_state_change = time.time()
                logger.info(f"熔断器{self.name}进入半开状态")
            else:
                # 仍然熔断，直接返回异常
                remaining_time = self._get_remaining_recovery_time()
                raise CircuitBreakerError(
                    f"熔断器{self.name}处于熔断状态，剩余恢复时间: {remaining_time}秒",
                    CircuitState.OPEN,
                    self.name
                )

        # 尝试调用函数
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """
        是否应该尝试重置熔断器

        Returns:
            True - 应该尝试重置，False - 继续熔断
        """
        if self.last_failure_time is None:
            return False

        current_time = time.time()
        time_since_failure = current_time - self.last_failure_time

        return time_since_failure >= self.recovery_timeout

    def _get_remaining_recovery_time(self) -> int:
        """
        获取剩余的恢复时间

        Returns:
            剩余时间（秒）
        """
        if self.last_failure_time is None:
            return 0

        elapsed = time.time() - self.last_failure_time
        remaining = max(0, self.recovery_timeout - elapsed)
        return int(remaining)

    def _on_success(self):
        """处理成功调用"""
        with self.lock:
            self.successful_calls += 1
            self.failure_count = 0

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    # 达到成功阈值，恢复到CLOSED状态
                    self.state = CircuitState.CLOSED
                    self.last_state_change = time.time()
                    logger.info(f"熔断器{self.name}恢复正常 (CLOSED状态)")
            elif self.state == CircuitState.CLOSED:
                # 正常状态下的成功，重置失败计数
                pass

    def _on_failure(self):
        """处理失败调用"""
        with self.lock:
            self.failed_calls += 1
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                # 半开状态下的失败，直接熔断
                self.state = CircuitState.OPEN
                self.last_state_change = time.time()
                logger.warning(f"熔断器{self.name}在半开状态下失败，重新回到熔断状态")
            elif self.state == CircuitState.CLOSED:
                # 正常状态下的失败
                if self.failure_count >= self.failure_threshold:
                    # 达到失败阈值，触发熔断
                    self.state = CircuitState.OPEN
                    self.last_state_change = time.time()
                    logger.warning(f"熔断器{self.name}触发熔断 (连续{self.failure_count}次失败)")

    def get_state(self) -> CircuitState:
        """获取当前状态"""
        with self.lock:
            return self.state

    def get_stats(self) -> Dict[str, Any]:
        """获取熔断器统计信息"""
        with self.lock:
            success_rate = self.successful_calls / max(1, self.total_calls)

            return {
                "name": self.name,
                "state": self.state.value,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": datetime.fromtimestamp(self.last_failure_time).isoformat() if self.last_failure_time else None,
                "last_state_change": datetime.fromtimestamp(self.last_state_change).isoformat(),
                "total_calls": self.total_calls,
                "successful_calls": self.successful_calls,
                "failed_calls": self.failed_calls,
                "success_rate": f"{success_rate:.2%}",
                "remaining_recovery_time": self._get_remaining_recovery_time()
            }

    def manual_reset(self):
        """手动重置熔断器"""
        with self.lock:
            original_state = self.state
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            self.last_state_change = time.time()

            logger.info(f"熔断器{self.name}已手动重置 (从{original_state.value} -> CLOSED)")

    def is_healthy(self) -> bool:
        """检查熔断器是否健康（即可以正常服务）"""
        return self.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN]

    def force_open(self):
        """强制进入熔断状态"""
        with self.lock:
            if self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN
                self.failure_count = self.failure_threshold
                self.last_failure_time = time.time()
                logger.warning(f"熔断器{self.name}已被强制进入熔断状态")

class CircuitBreakerManager:
    """熔断器管理器"""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.lock = threading.Lock()

    def get_circuit_breaker(self, provider: str) -> CircuitBreaker:
        """
        获取指定提供商的熔断器

        Args:
            provider: 数据提供商名称

        Returns:
            CircuitBreaker实例
        """
        if provider not in self.circuit_breakers:
            with self.lock:
                if provider not in self.circuit_breakers:
                    self.circuit_breakers[provider] = CircuitBreaker(provider)

        return self.circuit_breakers[provider]

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有熔断器的统计信息"""
        stats = {}
        for name, cb in self.circuit_breakers.items():
            stats[name] = cb.get_stats()
        return stats

    def reset_all(self):
        """重置所有熔断器"""
        with self.lock:
            for cb in self.circuit_breakers.values():
                cb.manual_reset()
        logger.info("所有熔断器已重置")

    def get_unhealthy_providers(self) -> List[str]:
        """获取不健康的提供商列表"""
        unhealthy = []
        for name, cb in self.circuit_breakers.items():
            if not cb.is_healthy():
                unhealthy.append(name)
        return unhealthy

    def force_open_all(self, reason: str = "manual"):
        """强制所有熔断器进入熔断状态"""
        with self.lock:
            for cb in self.circuit_breakers.values():
                cb.force_open()
        logger.warning(f"所有熔断器已被强制进入熔断状态，原因: {reason}")

# 全局熔断器管理器实例
circuit_breaker_manager = CircuitBreakerManager()

def circuit_break(provider: str):
    """
    熔断器装饰器

    Args:
        provider: 数据提供商名称

    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cb = circuit_breaker_manager.get_circuit_breaker(provider)
            return cb.call(func, *args, **kwargs)
        return wrapper
    return decorator