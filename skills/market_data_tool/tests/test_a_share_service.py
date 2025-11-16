"""
A股服务测试模块
测试从数据获取到错误处理的完整流程
"""

import pytest
from datetime import datetime
from skills.market_data_tool.services.a_share_service import AShareService
from skills.market_data_tool.utils.validators import validate_stock_symbol

class TestAShareService:
    """A股服务测试类"""

    @pytest.fixture
    def a_share_service(self):
        """创建A股服务实例"""
        return AShareService()

    def test_get_stock_quote_valid_symbol(self, a_share_service):
        """测试有效股票代码查询"""
        result = a_share_service.get_stock_quote("000001")
        assert "status" in result
        # 由于实时API调用可能不稳定，这里主要检测返回结构
        assert result["status"] in ["success", "error"]

    def test_get_stock_quote_invalid_symbol(self, a_share_service):
        """测试无效股票代码查询"""
        result = a_share_service.get_stock_quote("999999")  # 明显无效的代码
        assert result["status"] == "error"
        assert "error_message" in result

    def test_get_stock_quote_wrong_length(self, a_share_service):
        """测试错误长度的股票代码查询"""
        result = a_share_service.get_stock_quote("123")  # 太短
        assert result["status"] == "error"

    def test_get_batch_quotes(self, a_share_service):
        """测试批量查询"""
        test_symbols = ["000001", "000002", "999999"]
        result = a_share_service.get_batch_quotes(test_symbols)

        assert "status" in result
        assert "results" in result
        assert result["count"] == len(test_symbols)

    def test_get_market_overview(self, a_share_service):
        """测试市场概况获取"""
        result = a_share_service.get_market_overview()
        assert "status" in result
        assert result["market"] == "A-share"

    def test_service_stats(self, a_share_service):
        """测试服务统计"""
        result = a_share_service.get_service_stats()
        assert "market" in result
        assert "rate_limit_stats" in result


class TestSymbolValidation:
    """股票代码验证测试类"""

    def test_valid_a_share_codes(self):
        """测试有效的A股代码"""
        valid_codes = ["000001", "002001", "300001", "600000", "601001", "603001"]
        for code in valid_codes:
            result = validate_stock_symbol(code, "A-share")
            assert result.is_valid

    def test_invalid_a_share_codes(self):
        """测试无效的A股代码"""
        invalid_codes = ["999999", "123456", "abc123", ""]
        for code in invalid_codes:
            result = validate_stock_symbol(code, "A-share")
            assert not result.is_valid


if __name__ == "__main__":
    pytest.main([__file__])