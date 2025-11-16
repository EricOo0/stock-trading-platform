"""
测试数据源基类
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from skills.market_data_tool.data_sources.base import (
    BaseDataSource,
    DataSourceError,
    DataSourceTimeout,
    SymbolNotFoundError
)
from skills.market_data_tool.config import Config

class MockDataSource(BaseDataSource):
    """用于测试的模拟数据源"""

    def __init__(self, name="test_source", timeout=10, auto_succeed=True, delay=0):
        super().__init__(name, timeout)
        self.auto_succeed = auto_succeed
        self.delay = delay
        self.call_count = 0

    def get_stock_quote(self, symbol: str, market: str) -> dict:
        """模拟获取股票行情"""
        self.call_count += 1

        if self.delay > 0:
            time.sleep(self.delay)

        if not self.auto_succeed:
            raise Exception("模拟API错误")

        # 模拟不同市场的返回数据
        if market == "A-share":
            return {
                "symbol": symbol,
                "name": f"{symbol}股票名称",
                "price": 10.50,
                "change": 0.25,
                "change_percent": 2.44,
                "volume": 1250000,
                "market_cap": 1000000000,
                "update_time": datetime.now().isoformat()
            }
        elif market == "US":
            return {
                "symbol": symbol,
                "name": f"{symbol} Inc.",
                "price": 150.75,
                "change": -2.50,
                "change_percent": -1.63,
                "volume": 25000000,
                "market_cap": 2000000000000,
                "currency": "USD",
                "update_time": datetime.now().isoformat()
            }
        else:  # HK
            return {
                "symbol": symbol,
                "name": f"{symbol}公司",
                "price": 85.60,
                "change": 1.20,
                "change_percent": 1.42,
                "volume": 18000000,
                "market_cap": 850000000000,
                "currency": "HKD",
                "update_time": datetime.now().isoformat()
            }

    def validate_symbol(self, symbol: str, market: str) -> bool:
        """模拟股票代码验证"""
        config = Config()
        return config.validate_symbol_format(symbol, market)

import time  # Moved to top of test methods that need it

class TestDataSourceInit:
    """测试数据源初始化"""

    def test_base_datasource_init(self):
        """测试基础数据源初始化"""
        ds = MockDataSource("test_datasource", timeout=15)

        assert ds.name == "test_datasource"
        assert ds.timeout == 15
        assert ds.logger.name == "datasource.test_datasource"

    def test_default_timeout_value(self):
        """测试默认超时值"""
        ds = MockDataSource("test_datasource")
        assert ds.timeout == 10

import time  # Needed for timing tests

class TestDataSourceErrors:
    """测试数据源异常"""

    def test_data_source_error_creation(self):
        """测试数据源异常创建"""
        error = DataSourceError("测试消息", "test_provider", "TEST_ERROR")

        assert error.message == "测试消息"
        assert error.provider == "test_provider"
        assert error.error_code == "TEST_ERROR"
        assert str(error) == "测试消息"

    def test_data_source_timeout_error(self):
        """测试数据源超时异常"""
        error = DataSourceTimeout("test_provider", 30)

        assert error.error_code == "TIMEOUT"
        assert "test_provider" in error.message
        assert "30秒" in error.message

    def test_symbol_not_found_error(self):
        """测试股票代码不存在异常"""
        error = SymbolNotFoundError("INVALID123", "test_provider")

        assert error.error_code == "SYMBOL_NOT_FOUND"
        assert "INVALID123" in error.message
        assert "test_provider" in error.message

class TestGetStockQuote:
    """测试获取股票行情方法"""

    def test_get_stock_quote_success(self):
        """测试成功获取股票行情"""
        ds = MockDataSource("test_datasource")

        result = ds.get_stock_quote("000001", "A-share")

        assert result["symbol"] == "000001"
        assert result["name"] == "000001股票名称"
        assert result["price"] == 10.50
        assert result["change"] == 0.25
        assert result["change_percent"] == 2.44
        assert result["volume"] == 1250000
        assert result["market_cap"] == 1000000000
        assert "update_time" in result

    def test_get_different_market_data(self):
        """测试获取不同市场数据"""
        ds = MockDataSource("test_datasource")

        # A股
        result_a = ds.get_stock_quote("000001", "A-share")
        assert result_a["currency"] is None  # A股默认货币
        assert "公司" in result_a["name"]  # A股名称格式

        # 美股
        result_us = ds.get_stock_quote("AAPL", "US")
        assert result_us["currency"] == "USD"
        assert "Inc." in result_us["name"]  # 美股名称格式

        # 港股
        result_hk = ds.get_stock_quote("00700", "HK")
        assert result_hk["currency"] == "HKD"
        assert "公司" in result_hk["name"]  # 港股名称格式

    def test_get_stock_quote_with_timeout(self):
        """测试超时情况"""
        ds = MockDataSource("test_datasource", delay=0.5)  # 模拟延迟

        # 设置超时小于延迟
        ds.timeout = 0.1

        with pytest.raises(DataSourceTimeout):
            ds.get_stock_quote("000001", "A-share")

class TestSymbolValidation:
    """测试股票代码验证"""

    def test_valid_a_share_symbols(self):
        """测试有效的A股代码"""
        ds = MockDataSource("test_datasource")

        valid_symbols = ["000001", "002001", "300001", "600001", "601001", "603001"]
        for symbol in valid_symbols:
            result = ds.validate_symbol(symbol, "A-share")
            assert result is True, f"Symbol {symbol} should be valid"

    def test_invalid_a_share_symbols(self):
        """测试无效的A股代码"""
        ds = MockDataSource("test_datasource")

        invalid_symbols = ["00001", "0000001", "123456", "ABCDEF"]
        for symbol in invalid_symbols:
            result = ds.validate_symbol(symbol, "A-share")
            assert result is False, f"Symbol {symbol} should be invalid"

    def test_valid_us_symbols(self):
        """测试有效的美股代码"""
        ds = MockDataSource("test_datasource")

        valid_symbols = ["A", "AAPL", "GOOG", "TSLA", "MSFT"]
        for symbol in valid_symbols:
            result = ds.validate_symbol(symbol, "US")
            assert result is True, f"US Symbol {symbol} should be valid"

    def test_invalid_us_symbols(self):
        """测试无效的美股代码"""
        ds = MockDataSource("test_datasource")

        invalid_symbols = ["AAPL123", "TOOLONG", "", "12345"]
        for symbol in invalid_symbols:
            result = ds.validate_symbol(symbol, "US")
            assert result is False, f"US Symbol {symbol} should be invalid"

    def test_valid_hk_symbols(self):
        """测试有效的港股代码"""
        ds = MockDataSource("test_datasource")

        valid_symbols = ["00001", "00700", "03988", "09988"]
        for symbol in valid_symbols:
            result = ds.validate_symbol(symbol, "HK")
            assert result is True, f"HK Symbol {symbol} should be valid"

    def test_invalid_hk_symbols(self):
        """测试无效的港股代码"""
        ds = MockDataSource("test_datasource")

        invalid_symbols = ["10001", "0001", "0000001", "0ABCD"]
        for symbol in invalid_symbols:
            result = ds.validate_symbol(symbol, "HK")
            assert result is False, f"HK Symbol {symbol} should be invalid"

class TestMarketDetection:
    """测试市场自动检测"""

    def test_detect_a_share_market(self):
        """测试检测A股市场"""
        ds = MockDataSource("test_datasource")

        a_share_symbols = ["000001", "002001", "300001", "600001", "601001", "603001"]
        for symbol in a_share_symbols:
            market = ds._detect_market(symbol)
            assert market == "A-share", f"Symbol {symbol} should be detected as A-share"

    def test_detect_us_market(self):
        """测试检测美股市场"""
        ds = MockDataSource("test_datasource")

        us_symbols = ["A", "AAPL", "GOOG", "TSLA", "MSFT"]
        for symbol in us_symbols:
            market = ds._detect_market(symbol)
            assert market == "US", f"Symbol {symbol} should be detected as US"

    def test_detect_hk_market(self):
        """测试检测港股市场"""
        ds = MockDataSource("test_datasource")

        hk_symbols = ["00001", "00700", "03988", "09988"]
        for symbol in hk_symbols:
            market = ds._detect_market(symbol)
            assert market == "HK", f"Symbol {symbol} should be detected as HK"

    def test_default_to_a_share(self):
        """测试无法识别时默认到A股"""
        ds = MockDataSource("test_datasource")

        unknown_symbols = ["ABCDEF", "99999", "XXXXX"]
        for symbol in unknown_symbols:
            market = ds._detect_market(symbol)
            assert market == "A-share", f"Symbol {symbol} should default to A-share"

class TestBatchQuotes:
    """测试批量获取行情"""

    def test_batch_quotes_all_success(self):
        """测试批量获取全部成功的行情"""
        ds = MockDataSource("test_datasource")

        symbols = ["000001", "000002", "000003"]
        result = ds.get_batch_quotes(symbols)

        assert result["status"] == "success"
        assert result["requested_symbols"] == symbols
        assert len(result["successful_symbols"]) == 3
        assert len(result["failed_symbols"]) == 0
        assert result["success_rate"] == 1.0
        assert "data" in result
        assert "timestamp" in result

        # 验证每个股票的数据
        for symbol in symbols:
            assert symbol in result["data"]
            assert result["data"][symbol]["status"] == "success"
            assert "data" in result["data"][symbol]

    def test_batch_quotes_partial_success(self):
        """测试批量获取部分成功的行情"""
        ds = MockDataSource("test_datasource", auto_succeed=False)

        symbols = ["000001", "INVALID", "000003"]
        result = ds.get_batch_quotes(symbols)

        assert result["status"] == "partial"
        assert result["requested_symbols"] == symbols
        assert len(result["successful_symbols"]) == 0  # 因为auto_succeed=False
        assert len(result["failed_symbols"]) == 3
        assert result["success_rate"] == 0.0

    def test_batch_quotes_empty_list(self):
        """测试空股票列表"""
        ds = MockDataSource("test_datasource")

        result = ds.get_batch_quotes([])

        assert result["status"] == "success"
        assert result["requested_symbols"] == []
        assert result["success_rate"] == 0  # 空列表，成功率0/0=0

    def test_batch_quotes_with_mixed_markets(self):
        """测试混合市场的批量获取"""
        ds = MockDataSource("test_datasource")

        symbols = ["000001", "AAPL", "00700"]  # A股、美股、港股
        result = ds.get_batch_quotes(symbols)

        assert len(result["data"]) == 3
        for symbol in symbols:
            assert symbol in result["data"]
            assert result["data"][symbol]["status"] == "success"

class TestErrorResponse:
    """测试错误响应"""

    def test_create_error_response_general_exception(self):
        """测试一般异常的错误响应"""
        ds = MockDataSource("test_datasource")
        import traceback

        exception = Exception("一般错误")
        response = ds._create_error_response("000001", exception)

        assert response["status"] == "error"
        assert response["symbol"] == "000001"
        assert response["error_code"] == "API_ERROR"
        assert response["error_message"] == "一般错误"
        assert response["data_source"] == "test_datasource"
        assert "timestamp" in response

    def test_create_error_response_timeout_exception(self):
        """测试超时异常的错误响应"""
        ds = MockDataSource("test_datasource")

        exception = DataSourceTimeout("test_datasource", 30)
        response = ds._create_error_response("000001", exception)

        assert response["error_code"] == "TIMEOUT"
        assert "请求超时" in response["error_message"]

    def test_create_error_response_symbol_not_found_exception(self):
        """测试股票代码不存在异常的错误响应"""
        ds = MockDataSource("test_datasource")

        exception = SymbolNotFoundError("INVALID123", "test_datasource")
        response = ds._create_error_response("INVALID123", exception)

        assert response["error_code"] == "SYMBOL_NOT_FOUND"
        assert "不存在" in response["error_message"]

class TestDatasourceIntegration:
    """测试数据源集成"""

    def test_full_data_flow(self):
        """测试完整数据流"""
        ds = MockDataSource("integration_test")

        # 1. 验证股票代码
        is_valid = ds.validate_symbol("000001", "A-share")
        assert is_valid is True

        # 2. 获取单个股票行情
        quote = ds.get_stock_quote("000001", "A-share")
        assert quote["symbol"] == "000001"
        assert quote["price"] > 0

        # 3. 批量获取股票行情
        symbols = ["000001", "000002"]
        batch_result = ds.get_batch_quotes(symbols)
        assert batch_result["status"] in ["success", "partial"]
        assert len(batch_result["data"]) == 2

    def test_market_detection_integration(self):
        """测试市场检测集成"""
        ds = MockDataSource("test_datasource")

        # 使用自动市场检测的批量调用
        mixed_symbols = ["000001", "AAPL", "00700"]
        result = ds.get_batch_quotes(mixed_symbols)

        assert result["status"] == "success"

        # 验证每个市场类型都被正确处理
        for symbol in mixed_symbols:
            quote_data = result["data"][symbol]["data"]
            assert quote_data["symbol"] == symbol

class TestPerformance:
    """测试性能相关的场景"""

    def test_fast_batch_query_performance(self):
        """测试快速批量查询性能"""
        ds = MockDataSource("test_datasource")
        symbols = [f"{i:06d}" for i in range(100, 110)]  # 10个A股代码

        start_time = time.time()
        result = ds.get_batch_quotes(symbols)
        end_time = time.time()

        assert result["status"] == "success"
        assert end_time - start_time < 1.0  # 应该在1秒内完成

    def test_timeout_handling_efficiency(self):
        """测试超时处理效率"""
        ds = MockDataSource("test_datasource", delay=0.5)  # 0.5秒延迟
        ds.timeout = 0.1  # 0.1秒超时

        start_time = time.time()

        try:
            ds.get_stock_quote("000001", "A-share")
            assert False, "应该发生超时"
        except DataSourceTimeout:
            pass  # 预期结果

        end_time = time.time()

        # 超时处理应该在合理时间内完成（小于1秒，考虑到处理开销）
        assert end_time - start_time < 1.0

class TestThreadSafety:
    """测试线程安全"""

    def test_concurrent_batch_queries(self):
        """测试并发的批量查询"""
        import threading

        ds = MockDataSource("test_datasource")
        results = []

        def worker(symbols):
            result = ds.get_batch_quotes(symbols)
            results.append(result)

        # 启动多个线程并行查询
        threads = []
        thread_symbols = [
            ["000001", "000002"],
            ["AAPL", "GOOG"],
            ["00700", "00001"]
        ]

        for symbols in thread_symbols:
            thread = threading.Thread(target=worker, args=(symbols,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有查询都成功
        assert len(results) == 3
        for result in results:
            assert result["status"] in ["success", "partial"]

    def test_concurrent_symbol_validation(self):
        """测试并发的股票代码验证"""
        import threading

        ds = MockDataSource("test_datasource")
        validation_results = []

        def worker(symbols, market):
            for symbol in symbols:
                is_valid = ds.validate_symbol(symbol, market)
                validation_results.append((symbol, is_valid))

        # 启动多个验证线程
        threads = []
        test_cases = [
            (["000001", "000002", "000003"], "A-share"),
            (["AAPL", "GOOG", "MSFT"], "US"),
            (["00700", "00001", "03988"], "HK")
        ]

        for symbols, market in test_cases:
            thread = threading.Thread(target=worker, args=(symbols, market))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证验证结果的一致性
        assert len(validation_results) == 9
        symbol_valid_pairs = {symbol: is_valid for symbol, is_valid in validation_results}

        # 验证一些已知的正确结果
        assert symbol_valid_pairs["000001"] is True
        assert symbol_valid_pairs["AAPL"] is True
        assert symbol_valid_pairs["00700"] is True

class TestErrorScenarios:
    """测试错误场景处理"""

    def test_abstract_methods_enforcement(self):
        """测试抽象方法强制执行"""
        # 直接实例化抽象类应该抛出异常
        with pytest.raises(TypeError):
            BaseDataSource("test")

    def test_invalid_market_handling(self):
        """测试无效市场处理"""
        ds = MockDataSource("test_datasource")

        # 使用无效市场应该导致验证失败
        is_valid = ds.validate_symbol("000001", "INVALID_MARKET")
        assert is_valid is False

        # 市场检测对无效代码应该返回默认值
        market = ds._detect_market("INVALID123")
        assert market == "A-share"  # 默认返回A股

    def test_empty_symbol_handling(self):
        """测试空股票代码处理"""
        ds = MockDataSource("test_datasource")

        # 空股票代码验证应该失败
        is_valid = ds.validate_symbol("", "A-share")
        assert is_valid is False

        # 空股票代码市场检测应该返回默认市场
        market = ds._detect_market("")
        assert market == "A-share"

    def test_unicode_symbol_handling(self):
        """测试Unicode股票代码处理"""
        ds = MockDataSource("test_datasource")

        # Unicode股票代码应该正常验证
        is_valid = ds.validate_symbol("🚀STOCK", "US")
        assert is_valid is False  # 应该不被识别为有效美股代码

class TestAbstractMethods:
    """测试抽象方法"""

    def test_abstract_methods_defined(self):
        """测试抽象方法已定义"""
        # 验证抽象方法存在
        assert hasattr(BaseDataSource, 'get_stock_quote')
        assert hasattr(BaseDataSource, 'validate_symbol')
        assert hasattr(BaseDataSource, 'get_batch_quotes')
        assert hasattr(BaseDataSource, '_detect_market')
        assert hasattr(BaseDataSource, '_create_error_response')

        # 验证抽象方法不能直接被调用
        with pytest.raises(TypeError):
            BaseDataSource.get_stock_quote(None, "000001", "A-share")

        with pytest.raises(TypeError):
            BaseDataSource.validate_symbol(None, "000001", "A-share")

if __name__ == "__main__":
    pytest.main([__file__])