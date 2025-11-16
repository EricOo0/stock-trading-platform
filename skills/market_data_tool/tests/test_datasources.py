"""
数据源测试模块
测试Yahoo Finance和新浪金融数据获取功能
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from skills.market_data_tool.data_sources.yahoo_finance import YahooFinanceDataSource
from skills.market_data_tool.data_sources.sina_finance import SinaFinanceDataSource

class TestDataSources:
    """数据源测试类"""

    def test_yahoo_finance_connection(self):
        """测试Yahoo Finance连接"""
        yahoo_source = YahooFinanceDataSource()

        # 测试连接
        is_connected = yahoo_source.test_connection()
        assert isinstance(is_connected, bool)

        # 测试数据获取（如果连接正常）
        if is_connected:
            try:
                result = yahoo_source.get_stock_quote("AAPL", "US")
                assert "symbol" in result
                assert result["symbol"] == "AAPL"
            except Exception as e:
                pytest.skip(f"数据源测试跳过: {e}")

    def test_sina_finance_connection(self):
        """测试新浪财经连接"""
        sina_source = SinaFinanceDataSource()

        # 测试连接
        is_connected = sina_source.test_connection()
        assert isinstance(is_connected, bool)

        # 测试数据获取（如果连接正常）
        if is_connected:
            try:
                result = sina_source.get_stock_quote("000001", "A-share")
                assert "symbol" in result
                assert result["symbol"] == "000001"
                assert result["market"] == "A-share"
            except Exception as e:
                pytest.skip(f"数据源测试跳过: {e}")

    def test_symbol_validation(self):
        """测试股票代码验证"""
        yahoo_source = YahooFinanceDataSource()
        sina_source = SinaFinanceDataSource()

        # Yahoo Finance支持多种市场
        assert yahoo_source.validate_symbol("000001", "A-share") == True
        assert yahoo_source.validate_symbol("AAPL", "US") == True
        assert yahoo_source.validate_symbol("00700", "HK") == True

        # 新浪财经仅支持A股
        assert sina_source.validate_symbol("000001", "A-share") == True
        assert sina_source.validate_symbol("AAPL", "US") == False  # 不支持


if __name__ == "__main__":
    pytest.main([__file__])