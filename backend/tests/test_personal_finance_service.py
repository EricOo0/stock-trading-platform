import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.agents.personal_finance.models import AssetItem, PriceUpdateMap
from backend.app.services.personal_finance_service import update_prices

@pytest.mark.asyncio
async def test_update_prices_mock_logic():
    # Mock Sina and AkShare tools
    with patch("backend.app.services.personal_finance_service.SinaFinanceTool") as MockSina, \
         patch("backend.app.services.personal_finance_service.AkShareTool") as MockAkShare:
        
        # Setup Mock behaviors
        MockSina.get_stock_quote = AsyncMock(return_value={"price": 180.0, "change_percent": 0.05, "update_time": "2024-01-01T10:00:00Z"})
        MockAkShare.get_fund_nav = AsyncMock(return_value={"price": 1.5, "change_percent": 0.01, "update_time": "2024-01-01T10:00:00Z"})

        # Input assets
        assets = [
            AssetItem(symbol="AAPL", type="Stock", market="US", quantity=10),
            AssetItem(symbol="000001", type="Fund", market="CN", quantity=100),
            AssetItem(symbol="Unknown", type="Other", quantity=1) # Should be ignored
        ]

        # Execute
        result = await update_prices(assets)

        # Assertions
        assert isinstance(result, PriceUpdateMap)
        assert "AAPL" in result.prices
        assert result.prices["AAPL"].price == 180.0
        assert "000001" in result.prices
        assert result.prices["000001"].price == 1.5
        assert "Unknown" not in result.prices
