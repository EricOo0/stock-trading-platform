from fastapi.testclient import TestClient
import pytest
from sqlmodel import SQLModel, create_engine, Session
from backend.entrypoints.api.server import app
from backend.app.agents.personal_finance.models import PortfolioSnapshot, AssetItem
import backend.app.agents.personal_finance.db_models  # Import to register models

client = TestClient(app)

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_portfolio_persistence():
    test_user_id = "test_user_persistence"
    
    # 1. Initial Get (Should be empty)
    response = client.get(f"/api/personal-finance/portfolio?user_id={test_user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["assets"] == []
    assert data["cash_balance"] == 0.0
    
    # 2. Save Portfolio
    payload = {
        "assets": [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "type": "Stock",
                "quantity": 10,
                "cost_basis": 150.0,
                "current_price": 175.0,
                "total_value": 1750.0
            }
        ],
        "cash_balance": 5000.0,
        "query": "Analysis please"
    }
    
    response = client.post(f"/api/personal-finance/portfolio?user_id={test_user_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["assets"]) == 1
    assert data["assets"][0]["symbol"] == "AAPL"
    assert data["cash_balance"] == 5000.0
    # ID should be generated
    assert data["assets"][0]["id"] is not None
    
    # 3. Get Again (Should persist)
    response = client.get(f"/api/personal-finance/portfolio?user_id={test_user_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["assets"]) == 1
    assert data["assets"][0]["symbol"] == "AAPL"
    assert data["cash_balance"] == 5000.0
    
    # 4. Update (Overwrite)
    payload["assets"].append({
        "symbol": "BTC",
        "name": "Bitcoin",
        "type": "Crypto",
        "quantity": 0.5,
        "cost_basis": 20000.0,
        "current_price": 40000.0,
        "total_value": 20000.0
    })
    payload["cash_balance"] = 1000.0
    
    response = client.post(f"/api/personal-finance/portfolio?user_id={test_user_id}", json=payload)
    assert response.status_code == 200
    
    # 5. Verify Update
    response = client.get(f"/api/personal-finance/portfolio?user_id={test_user_id}")
    data = response.json()
    assert len(data["assets"]) == 2
    assert data["cash_balance"] == 1000.0

def test_shadow_portfolio_models(session):
    from backend.app.agents.personal_finance.db_models import ShadowPortfolio, ShadowAsset, PerformanceHistory
    
    # Test Shadow Portfolio creation
    shadow = ShadowPortfolio(user_id="test_user", cash_balance=10000.0)
    session.add(shadow)
    session.commit()
    session.refresh(shadow)
    assert shadow.id is not None
    assert shadow.cash_balance == 10000.0

    # Test Shadow Asset
    asset = ShadowAsset(portfolio_id=shadow.id, symbol="AAPL", quantity=10, avg_cost=150.0)
    session.add(asset)
    session.commit()
    
    # Test Performance History
    perf = PerformanceHistory(
        user_id="test_user", 
        date="2026-01-01", 
        nav_user=1.0, 
        nav_ai=1.0, 
        nav_sh=1.0, 
        nav_sz=1.0, 
        total_assets_user=10000.0,
        total_assets_ai=10000.0
    )
    session.add(perf)
    session.commit()
    assert perf.id is not None
