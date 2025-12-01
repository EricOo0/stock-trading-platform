"""
AkShare数据源测试
"""

import pytest
from unittest.mock import patch, MagicMock
from skills.market_data_tool.data_sources.akshare_data import AkShareDataSource
from skills.market_data_tool.data_sources.base import DataSourceError, SymbolNotFoundError

class TestAkShareDataSource:
    
    @pytest.fixture
    def data_source(self):
        return AkShareDataSource()

    @patch('akshare.stock_zh_a_spot_em')
    def test_get_stock_quote_success(self, mock_spot, data_source):
        # 模拟返回数据
        import pandas as pd
        mock_df = pd.DataFrame({
            '代码': ['000001'],
            '名称': ['平安银行'],
            '最新价': [10.5],
            '涨跌幅': [1.2],
            '涨跌额': [0.12],
            '成交量': [100000],
            '成交额': [1000000.0],
            '今开': [10.4],
            '最高': [10.6],
            '最低': [10.3],
            '昨收': [10.38]
        })
        mock_spot.return_value = mock_df
        
        result = data_source.get_stock_quote("000001", "A-share")
        
        assert result["symbol"] == "000001"
        assert result["current_price"] == 10.5
        assert result["name"] == "平安银行"
        assert result["source"] == "akshare"

    @patch('akshare.stock_zh_a_spot_em')
    def test_get_stock_quote_not_found(self, mock_spot, data_source):
        import pandas as pd
        mock_df = pd.DataFrame({
            '代码': ['000002'], # 不包含 000001
            '名称': ['万科A']
        })
        mock_spot.return_value = mock_df
        
        with pytest.raises(SymbolNotFoundError):
            data_source.get_stock_quote("000001", "A-share")

    def test_validate_symbol(self, data_source):
        assert data_source.validate_symbol("000001", "A-share") is True
        assert data_source.validate_symbol("AAPL", "US") is False
        assert data_source.validate_symbol("invalid", "A-share") is False

    @patch('akshare.stock_zh_a_hist')
    def test_get_historical_data(self, mock_hist, data_source):
        import pandas as pd
        mock_df = pd.DataFrame({
            '日期': ['2023-01-01', '2023-01-02'],
            '开盘': [10.0, 10.1],
            '最高': [10.2, 10.3],
            '最低': [9.9, 10.0],
            '收盘': [10.1, 10.2],
            '成交量': [1000, 1100]
        })
        mock_hist.return_value = mock_df
        
        result = data_source.get_historical_data("000001", "A-share")
        
        assert len(result) == 2
        assert result[0]['open'] == 10.0
        assert result[1]['close'] == 10.2
