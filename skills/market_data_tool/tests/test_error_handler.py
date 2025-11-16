"""
测试错误处理系统
"""

import pytest
import logging
from unittest.mock import Mock, patch
from datetime import datetime

from skills.market_data_tool.utils.error_handler import (
    MarketDataToolError,
    SymbolValidationError,
    RateLimitExceededError,
    DataSourceError,
    ServiceUnavailableError,
    ValidationError,
    create_error_response,
    create_success_response,
    create_partial_response,
    ErrorHandler,
    error_boundary
)

class TestMarketDataToolError:
    """测试市场数据工具异常基类"""

    def test_base_error_creation(self):
        """测试基础异常创建"""
        error = MarketDataToolError(
            code="TEST_ERROR",
            message="测试错误消息",
            suggestion="测试建议",
            context={"test": "context"}
        )

        assert error.code == "TEST_ERROR"
        assert error.message == "测试错误消息"
        assert error.suggestion == "测试建议"
        assert error.context == {"test": "context"}
        assert str(error) == "测试错误消息"

    def test_base_error_no_context(self):
        """测试没有上下文的异常创建"""
        error = MarketDataToolError(code="TEST_ERROR", message="测试消息")
        assert error.context == {}

class TestSpecificErrors:
    """测试特定错误类型"""

    def test_symbol_validation_error(self):
        """测试股票代码验证错误"""
        error = SymbolValidationError("000001", "格式错误")

        assert error.code == "INVALID_SYMBOL"
        assert "000001" in error.message
        assert error.context["symbol"] == "000001"
        assert error.context["details"] == "格式错误"
        assert "股票代码格式" in error.suggestion

    def test_rate_limit_exceeded_error(self):
        """测试限流错误"""
        error = RateLimitExceededError("A-share", 120, 0)

        assert error.code == "RATE_LIMITED"
        assert error.context["market"] == "A-share"
        assert error.context["rate_limit"] == 120
        assert error.context["remaining"] == 0
        assert "请求频率已达到上限" in error.message

    def test_data_source_error(self):
        """测试数据源错误"""
        original_error = Exception("连接超时")
        error = DataSourceError("yahoo", original_error)

        assert error.code == "API_ERROR"
        assert error.context["provider"] == "yahoo"
        assert error.context["original_error"] == "连接超时"
        assert "数据源" in error.suggestion or "datasource" in error.suggestion.lower()

    def test_service_unavailable_error(self):
        """测试服务不可用错误"""
        services = ["yahoo", "sina"]
        error = ServiceUnavailableError(services)

        assert error.code == "SERVICE_UNAVAILABLE"
        assert error.context["failed_services"] == services
        assert "所有数据源均不可用" in error.message
        assert "雅虎" in error.message or "yahoo" in error.message.lower()

    def test_validation_error(self):
        """测试数据验证错误"""
        error = ValidationError("price", 99999, "价格超出范围")

        assert error.code == "VALIDATION_ERROR"
        assert error.context["field"] == "price"
        assert error.context["value"] == 99999
        assert error.context["reason"] == "价格超出范围"

class TestResponseFunctions:
    """测试响应创建函数"""

    def test_create_error_response(self):
        """测试错误响应创建"""
        context = {"detail": "test"}
        response = create_error_response(
            symbol="000001",
            error_code="TEST_ERROR",
            error_message="测试错误",
            suggestion="测试建议",
            context=context,
            data_source="test_source"
        )

        assert response["status"] == "error"
        assert response["symbol"] == "000001"
        assert response["error_code"] == "TEST_ERROR"
        assert response["error_message"] == "测试错误"
        assert response["suggestion"] == "测试建议"
        assert response["context"] == context
        assert response["data_source"] == "test_source"
        assert "timestamp" in response

        # 验证时间戳格式
        try:
            datetime.fromisoformat(response["timestamp"])
        except ValueError:
            pytest.fail("时间戳格式无效")

    def test_create_success_response(self):
        """测试成功响应创建"""
        data = {"price": 10.5, "change": 0.2}
        response = create_success_response(
            symbol="000001",
            data=data,
            data_source="test_source",
            cache_hit=True,
            response_time_ms=150.5
        )

        assert response["status"] == "success"
        assert response["symbol"] == "000001"
        assert response["data"] == data
        assert response["data_source"] == "test_source"
        assert response["cache_hit"] is True
        assert response["response_time_ms"] == 150.5
        assert "timestamp" in response

    def test_create_partial_response(self):
        """测试部分成功响应创建"""
        results = [
            {"status": "success"},
            {"status": "error"},
            {"status": "success"}
        ]
        response = create_partial_response(results, "test_source", 500.0)

        assert response["status"] == "partial"
        assert response["count"] == 3
        assert response["successful_count"] == 2
        assert response["failed_count"] == 1
        assert response["success_rate"] == 2/3
        assert response["results"] == results
        assert response["data_source"] == "test_source"
        assert response["total_response_time_ms"] == 500.0
        assert "timestamp" in response

class TestErrorHandler:
    """测试错误处理器类"""

    def setup_method(self):
        """设置测试方法"""
        self.handler = ErrorHandler()

    def test_handle_market_data_tool_error(self):
        """测试处理市场数据工具异常"""
        exception = SymbolValidationError("000001")
        context = {"symbol": "000001", "provider": "test"}

        response = self.handler.handle_error(exception, context)

        assert response["status"] == "error"
        assert response["error_code"] == "INVALID_SYMBOL"
        assert response["symbol"] == "000001"
        assert response["data_source"] == "test"

    def test_handle_value_error(self):
        """测试处理值错误"""
        exception = ValueError("无效的输入")
        context = {"symbol": "000001"}

        response = self.handler.handle_error(exception, context)

        assert response["status"] == "error"
        assert response["error_code"] == "INVALID_INPUT"
        assert "输入参数错误" in response["error_message"]
        assert response["symbol"] == "000001"

    def test_handle_generic_exception(self):
        """测试处理通用异常"""
        exception = Exception("未知错误")
        context = {"symbol": "000001"}

        response = self.handler.handle_error(exception, context)

        assert response["status"] == "error"
        assert response["error_code"] == "INTERNAL_ERROR"
        assert "系统内部错误" in response["error_message"]
        assert response["symbol"] == "000001"

    def test_error_statistics(self):
        """测试错误统计"""
        handler = ErrorHandler()

        # 模拟多个错误
        handler.handle_error(SymbolValidationError("000001"))
        handler.handle_error(SymbolValidationError("000002"))
        handler.handle_error(ValueError("test"))
        handler.handle_error(Exception("test"))

        stats = handler.get_error_stats()

        assert stats["total_errors"] == 4
        assert stats["error_breakdown"]["SymbolValidationError"] == 2
        assert stats["error_breakdown"]["ValueError"] == 1
        assert stats["error_breakdown"]["Exception"] == 1
        assert "timestamp" in stats

    def test_error_logging(self):
        """测试错误日志记录"""
        with patch('logging.Logger.error') as mock_log:
            handler = ErrorHandler()
            exception = ValueError("测试错误")
            context = {"test": "context"}

            handler.handle_error(exception, context)

            # 验证有日志记录调用
            assert mock_log.called
            # 验证日志信息包含错误信息
            log_args = mock_log.call_args
            assert "ValueError: 测试错误" in str(log_args)

class TestErrorBoundary:
    """测试错误边界装饰器"""

    def test_error_boundary_success(self):
        """测试装饰器成功执行"""
        @error_boundary
        def success_function():
            return "success"

        result = success_function()
        assert result == "success"

    def test_error_boundary_catches_error(self):
        """测试装饰器捕获错误"""
        @error_boundary
        def error_function():
            raise ValueError("测试错误")

        result = error_function()

        assert result["status"] == "error"
        assert result["error_code"] == "INVALID_INPUT"

    def test_error_boundary_with_context(self):
        """测试装饰器记录上下文"""
        @error_boundary
        def function_with_args(x, y=10):
            raise Exception("测试异常")

        result = function_with_args(5, y=20)

        assert result["status"] == "error"
        assert "context" in result

class TestEdgeCases:
    """测试边界情况"""

    def test_empty_context_handling(self):
        """测试空上下文处理"""
        handler = ErrorHandler()
        response = handler.handle_error(Exception("test"), None)

        assert response["context"] is not None

    def test_unicode_characters_in_errors(self):
        """测试Unicode字符在错误消息中"""
        error = MarketDataToolError("TEST", "测试中文消息 🎉", "建议 🚀")

        assert error.message == "测试中文消息 🎉"
        assert error.suggestion == "建议 🚀"

    def test_response_timestamp_format(self):
        """测试响应时间戳格式"""
        response = create_error_response("000001", "TEST", "test")

        # 验证ISO格式时间戳
        try:
            dt = datetime.fromisoformat(response["timestamp"])
            assert isinstance(dt, datetime)
        except ValueError:
            pytest.fail("Invalid timestamp format")

    def test_large_context_data(self):
        """测试大上下文数据"""
        large_context = {f"key_{i}": f"value_{i}" for i in range(100)}

        handler = ErrorHandler()
        response = handler.handle_error(Exception("test"), large_context)

        # 确保上下文被正确传递
        assert response["context"]["key_0"] == "value_0"
        assert response["context"]["key_99"] == "value_99"

class TestIntegration:
    """集成测试"""

    def test_full_error_handling_flow(self):
        """测试完整的错误处理流程"""
        @error_boundary
        def problematic_function(symbol: str):
            raise SymbolValidationError(symbol)

        result = problematic_function("000000")

        assert result["status"] == "error"
        assert result["error_code"] == "INVALID_SYMBOL"
        assert result["symbol"] == "000000"
        assert "建议" in result

if __name__ == "__main__":
    pytest.main([__file__])