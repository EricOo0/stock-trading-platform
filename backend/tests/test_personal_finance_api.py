from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.entrypoints.api.server import app
from backend.app.agents.personal_finance.models import AssetItem, PriceUpdateMap, PriceUpdate

client = TestClient(app)

@patch("backend.entrypoints.api.routers.agent_personal_finance.update_prices")
def test_update_prices_endpoint(mock_update_prices):
    # Mock return value
    mock_response = PriceUpdateMap(
        prices={
            "sh600000": PriceUpdate(price=10.5, change_percent=1.2, update_time="2023-10-27 15:00:00"),
            "000001": PriceUpdate(price=1.234, change_percent=-0.5, update_time="2023-10-27 15:00:00")
        }
    )
    mock_update_prices.return_value = mock_response

    # Request data
    payload = {
        "assets": [
            {"id": "1", "symbol": "sh600000", "type": "Stock", "quantity": 100, "cost_basis": 10.0},
            {"id": "2", "symbol": "000001", "type": "Fund", "quantity": 1000, "cost_basis": 1.200}
        ]
    }

    response = client.post("/api/personal-finance/update-prices", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "prices" in data
    assert "sh600000" in data["prices"]
    assert data["prices"]["sh600000"]["price"] == 10.5
    assert "000001" in data["prices"]
    assert data["prices"]["000001"]["price"] == 1.234
    
    # Verify service was called correctly
    mock_update_prices.assert_called_once()
    args = mock_update_prices.call_args[0][0]
    assert len(args) == 2
    assert args[0].symbol == "sh600000"
    assert args[1].symbol == "000001"
