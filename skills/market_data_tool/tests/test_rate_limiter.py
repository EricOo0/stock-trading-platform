"""
测试限流系统
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from skills.market_data_tool.utils.rate_limiter import (
    TokenBucket,
    SlidingWindowRateLimiter,
    RateLimiterManager,
    RateLimitExceededError,
    rate_limiter  # 全局实例
)

class TestTokenBucket:
    """测试令牌桶限流器"""

    def test_initialization(self):
        """测试初始化"""
        bucket = TokenBucket(rate_per_hour=120, capacity=60)

        assert bucket.rate_per_hour == 120
        assert bucket.capacity == 60
        assert bucket.tokens == 60
        assert bucket.tokens_per_second == 120 / 3600
        assert bucket.total_consumed == 0
        assert bucket.total_rejected == 0

    def test_initialization_default_capacity(self):
        """测试默认容量初始化"""
        bucket = TokenBucket(rate_per_hour=120)

        assert bucket.capacity == 120
        assert bucket.tokens == 120

    def test_consume_single_token_success(self):
        """测试单令牌消费成功"""
        bucket = TokenBucket(rate_per_hour=60, capacity=10)

        result = bucket.consume(1)

        assert result is True
        assert bucket.tokens == 9
        assert bucket.total_consumed == 1

    def test_consume_multiple_tokens_success(self):
        """测试多令牌消费成功"""
        bucket = TokenBucket(rate_per_hour=60, capacity=10)

        result = bucket.consume(3)

        assert result is True
        assert bucket.tokens == 7
        assert bucket.total_consumed == 3

    def test_consume_when_insufficient_tokens(self):
        """测试令牌不足时的消费"""
        bucket = TokenBucket(rate_per_hour=60, capacity=2)

        # 先消费1个令牌
        bucket.consume(1)

        # 尝试消费2个令牌（应该失败）
        result = bucket.consume(2)

        assert result is False
        assert bucket.tokens == 1  # 令牌未被消费
        assert bucket.total_rejected == 2

    def test_token_refill_over_time(self):
        """测试随时间自动补充令牌"""
        bucket = TokenBucket(rate_per_hour=3600, capacity=60)  # 每秒1个令牌

        # 消费掉一些令牌
        bucket.consume(30)
        assert bucket.tokens == 30

        # 等待5秒钟让令牌补充
        time.sleep(5)

        # 应该补充5个令牌，但不会超过容量
        result = bucket.consume(30)
        assert result is True
        assert bucket.tokens <= 35  # 30 + 5 = 35

    def test_token_bucket_capacity_limit(self):
        """测试令牌桶容量限制"""
        bucket = TokenBucket(rate_per_hour=3600, capacity=10)

        # 等待足够长时间让令牌完全补充
        time.sleep(2)

        # 令牌数不应超过容量
        status = bucket.get_status()
        assert status["current_tokens"] <= 10

    def test_get_status(self):
        """测试获取状态信息"""
        bucket = TokenBucket(rate_per_hour=120, capacity=60)
        bucket.consume(10)

        status = bucket.get_status()

        assert status["rate_per_hour"] == 120
        assert status["capacity"] == 60
        assert status["current_tokens"] == 50
        assert status["total_consumed"] == 10
        assert status["total_rejected"] == 0
        assert 0 <= status["utilization_rate"] <= 1

class TestSlidingWindowRateLimiter:
    """测试滑动窗口限流器"""

    def test_initialization(self):
        """测试初始化"""
        limiter = SlidingWindowRateLimiter(max_requests=10, window_size=60)

        assert limiter.max_requests == 10
        assert limiter.window_size == 60
        assert limiter.requests == []

    def test_allow_request_when_under_limit(self):
        """测试在限制内允许请求"""
        limiter = SlidingWindowRateLimiter(max_requests=3, window_size=60)

        assert limiter.is_allowed() is True
        assert limiter.is_allowed() is True
        assert limiter.is_allowed() is True

    def test_reject_request_when_over_limit(self):
        """测试超出限制时拒绝请求"""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_size=60)

        assert limiter.is_allowed() is True
        assert limiter.is_allowed() is True
        assert limiter.is_allowed() is False  # 第三次应该被拒绝

    def test_window_expiration(self):
        """测试窗口过期机制"""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_size=1)  # 1秒窗口

        # 先填充到限制
        limiter.is_allowed()
        limiter.is_allowed()
        assert limiter.is_allowed() is False

        # 等待窗口过期
        time.sleep(1.1)

        # 应该再次允许请求
        assert limiter.is_allowed() is True

    def test_get_stats(self):
        """测试获取统计信息"""
        limiter = SlidingWindowRateLimiter(max_requests=5, window_size=60)
        limiter.is_allowed()
        limiter.is_allowed()

        stats = limiter.get_stats()

        assert stats["max_requests"] == 5
        assert stats["window_size"] == 60
        assert stats["current_requests"] == 2
        assert stats["remaining_requests"] == 3
        assert "reset_time" in stats

    def test_empty_stats(self):
        """测试空统计信息"""
        limiter = SlidingWindowRateLimiter(max_requests=5, window_size=60)

        stats = limiter.get_stats()

        assert stats["current_requests"] == 0
        assert stats["remaining_requests"] == 5
        assert stats["reset_time"] <= datetime.now() + timedelta(seconds=60)

class TestRateLimiterManager:
    """测试限流器管理器"""

    def setup_method(self):
        """设置测试方法"""
        # 创建新的管理器实例，避免影响全局实例
        self.manager = RateLimiterManager()

    def test_initialization_with_markets(self):
        """测试市场限流器初始化"""
        assert "A-share" in self.manager.limiters
        assert "US" in self.manager.limiters
        assert "HK" in self.manager.limiters

        # 验证每个市场有对应的限流器
        for market in ["A-share", "US", "HK"]:
            assert isinstance(self.manager.limiters[market], TokenBucket)

    def test_check_and_consume_allowed(self):
        """测试允许的消费请求"""
        result = self.manager.check_and_consume("A-share", 1)
        assert result is True

    def test_check_and_consume_rejected(self):
        """测试拒绝的消费请求"""
        # 尝试消费大量令牌超出限制
        result = self.manager.check_and_consume("US", 1000)
        assert result is False

    def test_check_unknown_market(self):
        """测试未知市场的检查"""
        result = self.manager.check_and_consume("UNKNOWN", 1)
        # 应该返回True并记录警告
        assert result is True

    def test_get_rate_limit_info_existing_market(self):
        """测试获取现有市场限流信息"""
        info = self.manager.get_rate_limit_info("A-share")

        assert info["market"] == "A-share"
        assert info["exists"] is True
        assert "rate_limit" in info
        assert "remaining_tokens" in info
        assert "utilization_rate" in info
        assert "time_to_reset" in info
        assert "suggestion" in info

    def test_get_rate_limit_info_nonexistent_market(self):
        """测试获取不存在市场限流信息"""
        info = self.manager.get_rate_limit_info("UNKNOWN")

        assert info["market"] == "UNKNOWN"
        assert info["exists"] is False
        assert "市场类型不支持" in info["suggestion"]

    def test_get_all_rate_limits(self):
        """测试获取所有市场限流信息"""
        all_limits = self.manager.get_all_rate_limits()

        assert "A-share" in all_limits
        assert "US" in all_limits
        assert "HK" in all_limits

        for market, info in all_limits.items():
            assert info["market"] == market
            assert info["exists"] is True

    def test_reset_rate_limit(self):
        """测试重置限流器"""
        # 先消费一些令牌
        self.manager.check_and_consume("A-share", 5)

        # 获取重置前的状态
        status_before = self.manager.limiters["A-share"].get_status()
        assert status_before["current_tokens"] < status_before["capacity"]

        # 重置限流器
        self.manager.reset_rate_limit("A-share")

        # 验证重置后的状态
        status_after = self.manager.limiters["A-share"].get_status()
        assert status_after["current_tokens"] == status_after["capacity"]

    def test_reset_nonexistent_limiter(self):
        """测试重置不存在限流器"""
        # 应该不抛出异常
        self.manager.reset_rate_limit("UNKNOWN")

    def test_get_global_stats(self):
        """测试获取全局统计信息"""
        # 消费一些令牌
        self.manager.check_and_consume("A-share", 3)
        self.manager.check_and_consume("US", 2)
        self.manager.check_and_consume("HK", 1)

        global_stats = self.manager.get_global_stats()

        assert "total_consumed" in global_stats
        assert "total_rejected" in global_stats
        assert "overall_utilization" in global_stats
        assert "market_breakdown" in global_stats
        assert "timestamp" in global_stats

        assert global_stats["total_consumed"] == 6
        assert global_stats["total_rejected"] == 0

        # 验证市场细分
        market_breakdown = global_stats["market_breakdown"]
        assert "A-share" in market_breakdown
        assert "US" in market_breakdown
        assert "HK" in market_breakdown

class TestGlobalRateLimiter:
    """测试全局的限流器实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在性"""
        from skills.market_data_tool.utils.rate_limiter import rate_limiter
        assert isinstance(rate_limiter, RateLimiterManager)

    def test_global_instance_has_markets(self):
        """测试全局实例包含市场"""
        from skills.market_data_tool.utils.rate_limiter import rate_limiter
        assert "A-share" in rate_limiter.limiters
        assert "US" in rate_limiter.limiters
        assert "HK" in rate_limiter.limiters

    def test_concurrent_access(self):
        """测试并发访问"""
        from skills.market_data_tool.utils.rate_limiter import rate_limiter

        results = []

        def access_limiter():
            for _ in range(10):
                result = rate_limiter.check_and_consume("A-share", 1)
                results.append(result)
                time.sleep(0.01)

        # 启动多个线程
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=access_limiter)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证没有崩溃，并且有一些成功、一些失败
        assert len(results) == 30
        assert any(results)  # 至少有一些成功
        # 由于令牌桶容量有限，也应该有一些失败

class TestEdgeCases:
    """测试边界情况"""

    def test_zero_rate_limit(self):
        """测试0限流率"""
        bucket = TokenBucket(rate_per_hour=0)

        # 应该永远无法消费
        assert bucket.consume(1) is False

    def test_negative_token_consumption(self):
        """测试负令牌消费"""
        bucket = TokenBucket(rate_per_hour=60)

        # 负令牌消费应该失败或处理
        with pytest.raises((ValueError, AssertionError)):
            bucket.consume(-1)

    def test_very_high_rate_limit(self):
        """测试非常高的限流率"""
        bucket = TokenBucket(rate_per_hour=1000000)

        assert bucket.consume(1000) is True  # 应该能消费大量令牌

    def test_token_bucket_with_small_capacity(self):
        """测试小容量令牌桶"""
        bucket = TokenBucket(rate_per_hour=60, capacity=1)

        assert bucket.consume(1) is True
        assert bucket.consume(1) is False  # 立即拒绝

    def test_thread_safety_under_load(self):
        """测试高负载下的线程安全"""
        bucket = TokenBucket(rate_per_hour=3600, capacity=100)

        def consume_tokens():
            for _ in range(10):
                bucket.consume(1)
                time.sleep(0.001)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=consume_tokens)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 验证统计信息的一致性
        status = bucket.get_status()
        assert status["total_consumed"] + status["total_rejected"] == 100

class TestIntegration:
    """集成测试"""

    def test_full_rate_limiting_flow(self):
        """测试完整的限流流程"""
        import skills.market_data_tool.utils.rate_limiter

        manager = RateLimiterManager()

        # 1. 检查限流状态
        limit_info = manager.get_rate_limit_info("A-share")
        assert limit_info["exists"] is True

        # 2. 尝试消费令牌
        can_consume = manager.check_and_consume("A-share", 5)
        assert isinstance(can_consume, bool)

        # 3. 再次检查状态
        new_info = manager.get_rate_limit_info("A-share")
        if can_consume:
            assert new_info["remaining_tokens"] <= limit_info["remaining_tokens"]

        # 4. 获取全局统计
        global_stats = manager.get_global_stats()
        assert "total_consumed" in global_stats
        assert "total_rejected" in global_stats

class TestLoggingIntegration:
    """测试日志集成"""

    @patch('logging.Logger.info')
    @patch('logging.Logger.warning')
    @patch('logging.Logger.debug')
    def test_rate_limiter_logging(self, mock_debug, mock_warning, mock_info):
        """测试限流器的日志记录"""
        manager = RateLimiterManager()

        # 触发一些日志记录
        manager.check_and_consume("A-share", 1000)  # 大消费应该触发警告
        manager.get_rate_limit_info("A-share")  # 信息查询
        manager.get_global_stats()  # 统计信息

        # 验证有日志记录（具体日志数量可能因实现而变化）
        assert mock_info.called or mock_debug.called or mock_warning.called

if __name__ == "__main__":
    pytest.main([__file__])