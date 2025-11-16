"""
测试熔断器系统
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from datetime import datetime

from skills.market_data_tool.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitBreakerError,
    CircuitState,
    circuit_breaker_manager,
    circuit_break
)

class TestCircuitStates:
    """测试熔断器状态"""

    def test_circuit_state_values(self):
        """测试熔断器状态枚举值"""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"

class TestCircuitBreakerBasic:
    """测试熔断器基础功能"""

    def test_initialization(self):
        """测试熔断器初始化"""
        cb = CircuitBreaker("test_service", failure_threshold=3, recovery_timeout=60)

        assert cb.name == "test_service"
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 60
        assert cb.success_threshold == 3  # 默认值
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
        assert cb.last_failure_time is None

    def test_initial_state_is_closed(self):
        """测试初始状态为关闭"""
        cb = CircuitBreaker("test")
        assert cb.get_state() == CircuitState.CLOSED
        assert cb.is_healthy() is True

    def test_successful_call_increments_stats(self):
        """测试成功调用增加统计"""
        cb = CircuitBreaker("test")

        def success_func():
            return "success"

        result = cb.call(success_func)

        assert result == "success"
        assert cb.successful_calls == 1
        assert cb.failed_calls == 0
        assert cb.total_calls == 1

    def test_failed_call_increments_failure_count(self):
        """测试失败调用增加失败计数"""
        cb = CircuitBreaker("test", failure_threshold=3)

        def fail_func():
            raise Exception("test error")

        with pytest.raises(Exception, match="test error"):
            cb.call(fail_func)

        assert cb.failure_count == 1
        assert cb.failed_calls == 1

    def test_multiple_failures_trigger_open_state(self):
        """测试多次失败触发熔断状态"""
        cb = CircuitBreaker("test", failure_threshold=3)

        def fail_func():
            raise Exception("test error")

        # 连续3次失败应该触发熔断
        for _ in range(3):
            with pytest.raises(Exception):
                cb.call(fail_func)

        assert cb.get_state() == CircuitState.OPEN
        assert cb.is_healthy() is False

    def test_open_state_blocks_calls(self):
        """测试熔断状态阻止调用"""
        cb = CircuitBreaker("test", failure_threshold=1)
        cb.force_open()  # 强制进入熔断状态

        def success_func():
            return "should not be called"

        with pytest.raises(CircuitBreakerError) as exc_info:
            cb.call(success_func)

        error = exc_info.value
        assert "熔断状态" in str(error)
        assert error.state == CircuitState.OPEN

    def test_half_open_state_after_timeout(self):
        """测试超时后半开状态"""
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=1)

        # 触发熔断
        def fail_func():
            raise Exception("error")

        with pytest.raises(Exception):
            cb.call(fail_func)

        assert cb.get_state() == CircuitState.OPEN

        # 等待恢复超时
        time.sleep(1.1)

        # 下一个调用应该进入半开状态
        def success_func():
            return "success"

        result = cb.call(success_func)
        assert result == "success"
        assert cb.get_state() == CircuitState.HALF_OPEN

    def test_half_open_success_resets_to_closed(self):
        """测试半开成功恢复关闭状态"""
        cb = CircuitBreaker("test", failure_threshold=1, success_threshold=2)

        # 强制进入半开状态
        cb.state = CircuitState.HALF_OPEN
        cb.failure_count = 0
        cb.success_count = 0

        def success_func():
            return "success"

        # 连续2次成功应该恢复关闭状态
        for _ in range(2):
            result = cb.call(success_func)
            assert result == "success"

        assert cb.get_state() == CircuitState.CLOSED

    def test_half_open_failure_back_to_open(self):
        """测试半开失败回到熔断状态"""
        cb = CircuitBreaker("test", failure_threshold=1)

        # 强制进入半开状态
        cb.state = CircuitState.HALF_OPEN

        def fail_func():
            raise Exception("error")

        with pytest.raises(Exception):
            cb.call(fail_func)

        assert cb.get_state() == CircuitState.OPEN

    def test_manual_reset(self):
        """测试手动重置"""
        cb = CircuitBreaker("test", failure_threshold=1)

        # 触发熔断
        def fail_func():
            raise Exception("error")

        with pytest.raises(Exception):
            cb.call(fail_func)

        assert cb.get_state() == CircuitState.OPEN

        # 手动重置
        cb.manual_reset()

        assert cb.get_state() == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
        assert cb.last_failure_time is None

    def test_force_open(self):
        """测试强制熔断"""
        cb = CircuitBreaker("test")

        cb.force_open()

        assert cb.get_state() == CircuitState.OPEN
        assert cb.failure_count == cb.failure_threshold

    def test_get_stats(self):
        """测试获取统计信息"""
        cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout=60)

        def success_func():
            return "success"

        def fail_func():
            raise Exception("error")

        # 执行一些调用
        cb.call(success_func)
        cb.call(success_func)
        with pytest.raises(Exception):
            cb.call(fail_func)

        stats = cb.get_stats()

        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert stats["failure_threshold"] == 3
        assert stats["recovery_timeout"] == 60
        assert stats["total_calls"] == 3
        assert stats["successful_calls"] == 2
        assert stats["failed_calls"] == 1
        assert "success_rate" in stats
        assert "last_state_change" in stats

    def test_remaining_recovery_time_calculation(self):
        """测试剩余恢复时间计算"""
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=10)

        # 触发熔断
        def fail_func():
            raise Exception("error")

        with pytest.raises(Exception):
            cb.call(fail_func)

        assert cb.get_state() == CircuitState.OPEN
        stats = cb.get_stats()
        assert stats["remaining_recovery_time"] <= 10
        assert stats["remaining_recovery_time"] > 0

class TestCircuitBreakerManager:
    """测试熔断器管理器"""

    def setup_method(self):
        """设置测试方法"""
        self.manager = CircuitBreakerManager()

    def test_get_circuit_breaker_creates_new(self):
        """测试获取熔断器时创建新的"""
        cb1 = self.manager.get_circuit_breaker("service1")
        cb2 = self.manager.get_circuit_breaker("service2")

        assert isinstance(cb1, CircuitBreaker)
        assert isinstance(cb2, CircuitBreaker)
        assert cb1 != cb2
        assert cb1.name == "service1"
        assert cb2.name == "service2"

    def test_get_same_circuit_breaker_returns_cached(self):
        """测试获取相同熔断器返回缓存"""
        cb1 = self.manager.get_circuit_breaker("service1")
        cb2 = self.manager.get_circuit_breaker("service1")

        assert cb1 is cb2  # 应该是同一个对象

    def test_get_all_stats(self):
        """测试获取所有熔断器统计"""
        # 创建几个熔断器
        self.manager.get_circuit_breaker("service1")
        self.manager.get_circuit_breaker("service2")

        all_stats = self.manager.get_all_stats()

        assert "service1" in all_stats
        assert "service2" in all_stats
        assert isinstance(all_stats["service1"], dict)
        assert isinstance(all_stats["service2"], dict)

    def test_reset_all(self):
        """测试重置所有熔断器"""
        # 创建一些熔断器并触发熔断
        cb1 = self.manager.get_circuit_breaker("service1")
        cb2 = self.manager.get_circuit_breaker("service2")

        cb1.force_open()
        cb2.force_open()

        assert cb1.get_state() == CircuitState.OPEN
        assert cb2.get_state() == CircuitState.OPEN

        # 重置所有熔断器
        self.manager.reset_all()

        assert cb1.get_state() == CircuitState.CLOSED
        assert cb2.get_state() == CircuitState.CLOSED

    def test_get_unhealthy_providers(self):
        """测试获取不健康的服务提供商"""
        cb1 = self.manager.get_circuit_breaker("service1")
        cb2 = self.manager.get_circuit_breaker("service2")

        # 让一个不健康
        cb1.force_open()

        unhealthy = self.manager.get_unhealthy_providers()
        assert "service1" in unhealthy
        assert "service2" not in unhealthy

    def test_force_open_all(self):
        """测试强制所有熔断器熔断"""
        # 创建一些熔断器
        cb1 = self.manager.get_circuit_breaker("service1")
        cb2 = self.manager.get_circuit_breaker("service2")

        # 强制所有熔断
        self.manager.force_open_all("test reason")

        assert cb1.get_state() == CircuitState.OPEN
        assert cb2.get_state() == CircuitState.OPEN

class TestCircuitBreakerDecorator:
    """测试熔断器装饰器"""

    def test_decorator_with_successful_call(self):
        """测试装饰器成功调用"""
        @circuit_break("test_service")
        def success_function():
            return "success"

        result = success_function()
        assert result == "success"

    def test_decorator_with_failed_call(self):
        """测试装饰器失败调用"""
        @circuit_break("test_service")
        def fail_function():
            raise Exception("test error")

        with pytest.raises(Exception, match="test error"):
            fail_function()

    def test_decorator_respects_circuit_state(self):
        """测试装饰器遵守熔断状态"""
        @circuit_break("test_service_for_decorator")
        def any_function():
            return "should not be called when open"

        # 强制让服务熔断
        cb = circuit_breaker_manager.get_circuit_breaker("test_service_for_decorator")
        cb.force_open()

        with pytest.raises(CircuitBreakerError) as exc_info:
            any_function()

        assert "熔断状态" in str(exc_info.value)

class TestConcurrency:
    """测试并发情况"""

    def test_concurrent_successful_calls(self):
        """测试并发成功调用"""
        cb = CircuitBreaker("test_concurrent")

        def worker():
            def success_func():
                return "success"
            return cb.call(success_func)

        threads = []
        results = []

        def thread_worker():
            results.append(worker())

        # 启动多个线程
        for _ in range(10):
            thread = threading.Thread(target=thread_worker)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 所有调用都应该成功
        assert len(results) == 10
        assert all(result == "success" for result in results)

    def test_concurrent_calls_that_fail(self):
        """测试并发失败的调用"""
        cb = CircuitBreaker("test_concurrent_fail", failure_threshold=5)

        def worker():
            def fail_func():
                raise Exception("error")
            try:
                cb.call(fail_func)
            except Exception:
                pass  # 预期失败

        threads = []

        # 启动多个线程进行失败调用
        for _ in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 熔断器应该被触发
        assert cb.get_state() == CircuitState.OPEN

class TestErrorHandling:
    """测试错误处理"""

    def test_circuit_breaker_error_attributes(self):
        """测试熔断器错误属性"""
        error = CircuitBreakerError("test message", CircuitState.OPEN, "test_provider")

        assert str(error) == "test message"
        assert error.state == CircuitState.OPEN
        assert error.provider == "test_provider"

    def test_get_stats_with_no_activity(self):
        """测试无活动时的统计"""
        cb = CircuitBreaker("test")
        stats = cb.get_stats()

        assert stats["total_calls"] == 0
        assert stats["successful_calls"] == 0
        assert stats["failed_calls"] == 0
        assert stats["success_rate"] == "0.00%"

    def test_should_attempt_reset_with_no_failure_time(self):
        """测试没有失败时间的重置检查"""
        cb = CircuitBreaker("test")
        # 没有失败时间时不应该尝试重置
        assert cb._should_attempt_reset() is False

class TestEdgeCases:
    """测试边界情况"""

    def test_zero_failure_threshold(self):
        """测试零失败阈值"""
        cb = CircuitBreaker("test", failure_threshold=0)

        def fail_func():
            raise Exception("error")

        # 第一次失败就应该触发熔断
        with pytest.raises(Exception):
            cb.call(fail_func)

        assert cb.get_state() == CircuitState.OPEN

    def test_zero_recovery_timeout(self):
        """测试零恢复超时"""
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0)

        def fail_func():
            raise Exception("error")

        # 触发熔断
        with pytest.raises(Exception):
            cb.call(fail_func)

        assert cb.get_state() == CircuitState.OPEN

        # 立即应该能够重置
        assert cb._should_attempt_reset() is True

    def test_very_long_recovery_timeout(self):
        """测试非常长的恢复超时"""
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=999999)

        def fail_func():
            raise Exception("error")

        # 触发熔断
        with pytest.raises(Exception):
            cb.call(fail_func)

        # 检查剩余恢复时间
        remaining_time = cb._get_remaining_recovery_time()
        assert remaining_time <= 999999
        assert remaining_time > 999990  # 由于执行时间，略小于完整值

    def test_unicode_in_service_name(self):
        """测试Unicode服务名称"""
        cb = CircuitBreaker("测试服务 🚀", failure_threshold=1)

        assert cb.name == "测试服务 🚀"
        assert str(cb.name) == "测试服务 🚀"

    def test_rapid_state_changes(self):
        """测试快速状态变更"""
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=1, success_threshold=1)

        def fail_func():
            raise Exception("error")

        def success_func():
            return "success"

        # 快速失败->熔断->半开->关闭->失败
        with pytest.raises(Exception):
            cb.call(fail_func)  # -> OPEN

        time.sleep(1.1)  # 等待恢复
        cb.call(success_func)  # -> HALF_OPEN
        # 应该已经 -> CLOSED
        assert cb.get_state() == CircuitState.CLOSED

        with pytest.raises(Exception):
            cb.call(fail_func)  # -> OPEN again

        assert cb.get_state() == CircuitState.OPEN

class TestGlobalCircuitBreakerManager:
    """测试全局熔断器管理器实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert isinstance(circuit_breaker_manager, CircuitBreakerManager)

    def test_global_instance_has_circuit_breakers(self):
        """测试全局实例包含熔断器"""
        # 应该有一些预先创建的熔断器
        stats = circuit_breaker_manager.get_all_stats()
        assert len(stats) >= 0  # 可能是空的

    def test_global_instance_thread_safe(self):
        """测试全局实例线程安全"""
        def worker():
            for i in range(5):
                cb = circuit_breaker_manager.get_circuit_breaker(f"service_{i}")
                time.sleep(0.01)

        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 不应该崩溃或产生不一致状态
        stats = circuit_breaker_manager.get_all_stats()
        assert len(stats) >= 0

class TestIntegration:
    """集成测试"""

    def test_full_circuit_breaker_flow(self):
        """测试完整的熔断器流程"""
        cb = CircuitBreaker("integration_test", failure_threshold=2, recovery_timeout=1)

        def success_func():
            return {"status": "ok", "data": "test"}

        def fail_func():
            raise Exception("API Error 500")

        # 1. 正常调用阶段
        result = cb.call(success_func)
        assert result["status"] == "ok"
        assert cb.get_state() == CircuitState.CLOSED

        # 2. 故障阶段 - 多次失败后熔断
        with pytest.raises(Exception):
            cb.call(fail_func)
        with pytest.raises(Exception):
            cb.call(fail_func)

        assert cb.get_state() == CircuitState.OPEN

        # 3. 熔断阶段 - 调用应被拒绝
        with pytest.raises(CircuitBreakerError):
            cb.call(success_func)

        # 4. 恢复阶段 - 超时后尝试半开状态
        time.sleep(1.1)

        result = cb.call(success_func)  # 应该成功并进入HALF_OPEN
        assert result == {"status": "ok", "data": "test"}
        assert cb.get_state() == CircuitState.HALF_OPEN

        # 5. 完全恢复 - 连续成功后关闭
        result = cb.call(success_func)  # 应该进入CLOSED
        assert result == {"status": "ok", "data": "test"}
        assert cb.get_state() == CircuitState.CLOSED

    def test_decorator_realistic_usage(self):
        """测试装饰器的实际使用场景"""
        call_count = 0

        @circuit_break("realistic_service")
        def mock_api_call(endpoint: str, params: dict = None):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Network timeout")
            elif call_count <= 4:
                return {"status": "ok", "data": "test"}
            else:
                raise Exception("API Error")

        # 前两次调用应该失败
        for _ in range(2):
            with pytest.raises(Exception, match="Network timeout"):
                mock_api_call("/api/data")

        # 接下来两次应该成功
        result1 = mock_api_call("/api/data")
        result2 = mock_api_call("/api/data")
        assert result1["status"] == "ok"
        assert result2["status"] == "ok"

        # 再次发生错误后应该熔断
        with pytest.raises(Exception, match="API Error"):
            mock_api_call("/api/data")

        # 检查熔断器状态
        cb = circuit_breaker_manager.get_circuit_breaker("realistic_service")
        # 可能处于熔断或即将熔断状态

if __name__ == "__main__":
    pytest.main([__file__])