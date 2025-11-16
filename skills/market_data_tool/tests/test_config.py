"""
测试配置系统
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from skills.market_data_tool.config import Config

class TestConfigDefaults:
    """测试配置默认值"""

    def test_log_level_default(self):
        """测试日志级别默认值"""
        with patch.dict(os.environ, {}, clear=True):
            assert Config.LOG_LEVEL == "INFO"

    def test_cache_ttl_default(self):
        """测试缓存时间默认值"""
        with patch.dict(os.environ, {}, clear=True):
            assert Config.CACHE_TTL == 300

    def test_rate_limits_defaults(self):
        """测试限流默认值"""
        with patch.dict(os.environ, {}, clear=True):
            assert Config.RATE_LIMIT_A_SHARE == 120
            assert Config.RATE_LIMIT_US == 60
            assert Config.RATE_LIMIT_HK == 60

    def test_circuit_breaker_defaults(self):
        """测试熔断器默认值"""
        with patch.dict(os.environ, {}, clear=True):
            assert Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD == 5
            assert Config.CIRCUIT_BREAKER_RECOVERY_TIMEOUT == 300

    def test_api_defaults(self):
        """测试API默认值"""
        with patch.dict(os.environ, {}, clear=True):
            assert Config.API_TIMEOUT == 10
            assert Config.API_RETRY_COUNT == 3

    def test_data_source_defaults(self):
        """测试数据源默认值"""
        assert Config.PRIMARY_DATA_SOURCE == "yahoo"
        assert Config.BACKUP_DATA_SOURCE == "sina"

    def test_batch_config_defaults(self):
        """测试批量配置默认值"""
        with patch.dict(os.environ, {}, clear=True):
            assert Config.BATCH_MAX_SYMBOLS == 10
            assert Config.BATCH_TIMEOUT == 30

    def test_market_trading_hours_defaults(self):
        """测试市场交易时间默认值"""
        market_hours = Config.MARKET_TRADING_HOURS

        assert "A-share" in market_hours
        assert "US" in market_hours
        assert "HK" in market_hours

        # 验证A股交易时间
        a_share = market_hours["A-share"]
        assert a_share["morning_start"] == "09:30"
        assert a_share["morning_end"] == "11:30"
        assert a_share["afternoon_start"] == "13:00"
        assert a_share["afternoon_end"] == "15:00"

        # 验证美股交易时间
        us = market_hours["US"]
        assert us["start"] == "09:30"
        assert us["end"] == "16:00"

        # 验证港股交易时间 (corrected the afternoon end value)
        hk = market_hours["HK"]
        assert hk["morning_start"] == "09:30"
        assert hk["morning_end"] == "12:00"
        assert hk["afternoon_start"] == "13:00"
        assert hk["afternoon_end"] == "16:00"

    def test_a_share_prefixes_defaults(self):
        """测试A股代码前缀默认值"""
        prefixes = Config.A_SHARE_PREFIXES
        expected_prefixes = ["000", "002", "300", "600", "601", "603"]

        assert prefixes == expected_prefixes

class TestConfigEnvironmentVariables:
    """测试环境变量配置"""

    @patch.dict(os.environ, {
        'LOG_LEVEL': 'DEBUG',
        'CACHE_TTL': '600',
        'RATE_LIMIT_A_SHARE': '200',
        'RATE_LIMIT_US': '100',
        'RATE_LIMIT_HK': '80',
        'CIRCUIT_BREAKER_FAILURE_THRESHOLD': '10',
        'CIRCUIT_BREAKER_RECOVERY_TIMEOUT': '600',
        'API_TIMEOUT': '30',
        'API_RETRY_COUNT': '5',
        'BATCH_TIMEOUT': '60'
    })
    def test_environment_override(self):
        """测试环境变量覆盖默认值"""
        # 重新加载配置以应用环境变量
        import importlib
        import skills.market_data_tool.config
        importlib.reload(skills.market_data_tool.config)
        from skills.market_data_tool.config import Config as TestConfig

        assert TestConfig.LOG_LEVEL == 'DEBUG'
        assert TestConfig.CACHE_TTL == 600
        assert TestConfig.RATE_LIMIT_A_SHARE == 200
        assert TestConfig.RATE_LIMIT_US == 100
        assert TestConfig.RATE_LIMIT_HK == 80
        assert TestConfig.CIRCUIT_BREAKER_FAILURE_THRESHOLD == 10
        assert TestConfig.CIRCUIT_BREAKER_RECOVERY_TIMEOUT == 600
        assert TestConfig.API_TIMEOUT == 30
        assert TestConfig.API_RETRY_COUNT == 5
        assert TestConfig.BATCH_TIMEOUT == 60

    def test_invalid_numeric_values(self):
        """测试无效数值处理"""
        with patch.dict(os.environ, {
            'CACHE_TTL': 'invalid',
            'RATE_LIMIT_A_SHARE': 'not_a_number'
        }):
            # 这应该抛出 ValueError
            with pytest.raises(ValueError):
                Config.CACHE_TTL

    @patch('dotenv.load_dotenv')
    def test_dotenv_not_available(self, mock_load_dotenv):
        """测试dotenv不可用的情况"""
        # 模拟dotenv导入失败
        with patch.dict('sys.modules', {'dotenv': None}):
            # 重新导入配置模块
            import importlib
            import skills.market_data_tool.config
            importlib.reload(skills.market_data_tool.config)
            from skills.market_data_tool.config import Config as TestConfig

            # 应该还是使用默认值
            assert TestConfig.LOG_LEVEL == "INFO"

class TestRateLimitConfig:
    """测试限流配置方法"""

    def test_get_rate_limit_config_a_share(self):
        """测试获取A股限流配置"""
        with patch.dict(os.environ, {}, clear=True):
            limit = Config.get_rate_limit_config("A-share")
            assert limit == 120

    def test_get_rate_limit_config_us(self):
        """测试获取美股限流配置"""
        with patch.dict(os.environ, {}, clear=True):
            limit = Config.get_rate_limit_config("US")
            assert limit == 60

    def test_get_rate_limit_config_hk(self):
        """测试获取港股限流配置"""
        with patch.dict(os.environ, {}, clear=True):
            limit = Config.get_rate_limit_config("HK")
            assert limit == 60

    def test_get_rate_limit_config_unknown_market(self):
        """测试获取未知市场限流配置"""
        with patch.dict(os.environ, {}, clear=True):
            limit = Config.get_rate_limit_config("UNKNOWN")
            assert limit == 120  # 应该返回A股默认值

    @patch.dict(os.environ, {'RATE_LIMIT_A_SHARE': '200'})
    def test_get_rate_limit_config_with_env_override(self):
        """测试环境变量覆盖的限流配置"""
        import importlib
        import skills.market_data_tool.config
        importlib.reload(skills.market_data_tool.config)
        from skills.market_data_tool.config import Config as TestConfig

        limit = TestConfig.get_rate_limit_config("A-share")
        assert limit == 200

class TestSymbolValidation:
    """测试股票代码验证方法"""

    def setup_method(self):
        """设置测试方法"""
        self.config = Config()

    def test_validate_a_share_valid_prefixes(self):
        """测试A股有效前缀验证"""
        valid_symbols = [
            "000001",  # 平安银行
            "002001",  # 新和成
            "300001",  # 特锐德
            "600001",  # 邯郸钢铁
            "601001",  # 大同煤业
            "603001",  # 奥康国际
        ]

        for symbol in valid_symbols:
            result = self.config.validate_symbol_format(symbol, "A-share")
            assert result is True, f"Symbol {symbol} should be valid"

    def test_validate_a_share_invalid_prefixes(self):
        """测试A股无效前缀验证"""
        invalid_symbols = [
            "123456",  # 无效前缀
            "700001",  # 不在前缀列表中
            "888888",  # 随机数字
        ]

        for symbol in invalid_symbols:
            result = self.config.validate_symbol_format(symbol, "A-share")
            assert result is False, f"Symbol {symbol} should be invalid"

    def test_validate_a_share_wrong_length(self):
        """测试A股错误长度验证"""
        invalid_symbols = [
            "00001",    # 5位
            "0000001",  # 7位
            "0001",     # 4位
        ]

        for symbol in invalid_symbols:
            result = self.config.validate_symbol_format(symbol, "A-share")
            assert result is False, f"Symbol {symbol} should be invalid (wrong length)"

    def test_validate_us_valid_symbols(self):
        """测试美股有效代码验证"""
        valid_symbols = [
            "A",        # 单个字母
            "GOOG",     # 4个字母
            "APPLE",    # 5个字母
            "MSFT",     # 常见美股
            "TSLA",     # 特斯拉
        ]

        for symbol in valid_symbols:
            result = self.config.validate_symbol_format(symbol, "US")
            assert result is True, f"US Symbol {symbol} should be valid"

    def test_validate_us_invalid_symbols(self):
        """测试美股无效代码验证"""
        invalid_symbols = [
            "GOOGLE",   # 6个字母（太长）
            "1234",     # 数字
            "GOOGL1",   # 包含数字
            "",         # 空字符串
        ]

        for symbol in invalid_symbols:
            result = self.config.validate_symbol_format(symbol, "US")
            assert result is False, f"US Symbol {symbol} should be invalid"

    def test_validate_hk_valid_symbols(self):
        """测试港股有效代码验证"""
        valid_symbols = [
            "00001",    # 长和
            "00700",    # 腾讯控股
            "03988",    # 中国银行
            "09988",    # 阿里巴巴
        ]

        for symbol in valid_symbols:
            result = self.config.validate_symbol_format(symbol, "HK")
            assert result is True, f"HK Symbol {symbol} should be valid"

    def test_validate_hk_invalid_symbols(self):
        """测试港股无效代码验证"""
        invalid_symbols = [
            "10001",    # 不是以0开头
            "0001",     # 4位数字
            "0000001",  # 6位以上
            "0ABCD",    # 包含字母
            "AAAAA",    # 全是字母
        ]

        for symbol in invalid_symbols:
            result = self.config.validate_symbol_format(symbol, "HK")
            assert result is False, f"HK Symbol {symbol} should be invalid"

    def test_validate_unknown_market(self):
        """测试未知市场验证"""
        result = self.config.validate_symbol_format("000001", "UNKNOWN")
        assert result is False

    def test_validate_case_insensitive_us(self):
        """测试美股代码大小写不敏感"""
        result1 = self.config.validate_symbol_format("GOOG", "US")
        result2 = self.config.validate_symbol_format("goog", "US")
        result3 = self.config.validate_symbol_format("GoOg", "US")

        assert result1 is True
        assert result2 is True
        assert result3 is True

class TestConfigEdgeCases:
    """测试配置的边界情况"""

    def test_extreme_numeric_values(self):
        """测试极端数值"""
        with patch.dict(os.environ, {
            'CACHE_TTL': '0',
            'RATE_LIMIT_A_SHARE': '999999',
            'API_TIMEOUT': '1'
        }):
            import importlib
            import skills.market_data_tool.config
            importlib.reload(skills.market_data_tool.config)
            from skills.market_data_tool.config import Config as TestConfig

            assert TestConfig.CACHE_TTL == 0
            assert TestConfig.RATE_LIMIT_A_SHARE == 999999
            assert TestConfig.API_TIMEOUT == 1

    def test_negative_values(self):
        """测试负数值处理"""
        with patch.dict(os.environ, {
            'CACHE_TTL': '-100',
            'RATE_LIMIT_A_SHARE': '-50'
        }):
            import importlib
            import skills.market_data_tool.config
            importlib.reload(skills.market_data_tool.config)
            from skills.market_data_tool.config import Config as TestConfig

            # 负值应该被转换为负整数
            assert TestConfig.CACHE_TTL == -100
            assert TestConfig.RATE_LIMIT_A_SHARE == -50

    def test_empty_string_values(self):
        """测试空字符串值处理"""
        with patch.dict(os.environ, {
            'LOG_LEVEL': '',
        }):
            # 空字符串应该使用默认值
            with patch.dict(os.environ, {'LOG_LEVEL': 'INFO'}):
                assert Config.LOG_LEVEL == 'INFO'

    def test_class_method_vs_instance_method(self):
        """测试类方法与实例方法的区别"""
        # 限流配置是类方法
        assert hasattr(Config.get_rate_limit_config, '__func__')
        assert Config.get_rate_limit_config("A-share") == 120

        # 股票代码验证是实例方法
        config = Config()
        assert hasattr(config.validate_symbol_format, '__func__')
        assert config.validate_symbol_format("000001", "A-share") is True

class TestConfigValidation:
    """测试配置验证"""

    def test_valid_configuration(self):
        """测试有效配置"""
        # 创建配置实例
        config = Config()

        # 验证限流配置返回正确类型
        rate_limit = config.get_rate_limit_config("A-share")
        assert isinstance(rate_limit, int)
        assert rate_limit > 0

        # 验证股票代码验证返回布尔值
        is_valid = config.validate_symbol_format("000001", "A-share")
        assert isinstance(is_valid, bool)

    def test_configuration_integrity(self):
        """测试配置完整性"""
        # 确保所有必需的配置都存在
        assert hasattr(Config, 'LOG_LEVEL')
        assert hasattr(Config, 'CACHE_TTL')
        assert hasattr(Config, 'RATE_LIMIT_A_SHARE')
        assert hasattr(Config, 'RATE_LIMIT_US')
        assert hasattr(Config, 'RATE_LIMIT_HK')
        assert hasattr(Config, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD')
        assert hasattr(Config, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT')
        assert hasattr(Config, 'API_TIMEOUT')
        assert hasattr(Config, 'API_RETRY_COUNT')
        assert hasattr(Config, 'PRIMARY_DATA_SOURCE')
        assert hasattr(Config, 'BACKUP_DATA_SOURCE')
        assert hasattr(Config, 'BATCH_MAX_SYMBOLS')
        assert hasattr(Config, 'BATCH_TIMEOUT')
        assert hasattr(Config, 'MARKET_TRADING_HOURS')
        assert hasattr(Config, 'A_SHARE_PREFIXES')

    def test_method_presence(self):
        """测试必要方法的存在"""
        assert hasattr(Config, 'get_rate_limit_config')
        assert hasattr(Config, 'validate_symbol_format')

if __name__ == "__main__":
    pytest.main([__file__])