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

def test_shadow_portfolio_auto_creation():
    user_id = "test_user_shadow_auto"
    
    # 1. Create User Portfolio via API (which calls save_portfolio)
    payload = {
        "assets": [
            {
                "symbol": "AAPL",
                "type": "Stock",
                "quantity": 10,
                "cost_basis": 150.0,
                "current_price": 175.0,
                "total_value": 1750.0
            }
        ],
        "cash_balance": 5000.0
    }
    
    response = client.post(f"/api/personal-finance/portfolio?user_id={user_id}", json=payload)
    assert response.status_code == 200

    # 2. Verify Shadow Portfolio exists
    from backend.app.agents.personal_finance.db_models import ShadowPortfolio, ShadowAsset, PerformanceHistory
    from backend.app.agents.personal_finance.db import engine
    from sqlmodel import Session, select
    
    with Session(engine) as session:
        # Check Shadow Portfolio
        shadow = session.exec(select(ShadowPortfolio).where(ShadowPortfolio.user_id == user_id)).first()
        assert shadow is not None
        assert shadow.cash_balance == 5000.0
        
        # Check Shadow Assets
        assets = session.exec(select(ShadowAsset).where(ShadowAsset.portfolio_id == shadow.id)).all()
        assert len(assets) == 1
        assert assets[0].symbol == "AAPL"
        assert assets[0].quantity == 10
        
        # Check Initial Performance History
        perf = session.exec(select(PerformanceHistory).where(PerformanceHistory.user_id == user_id)).first()
        assert perf is not None
        assert perf.nav_user == 1.0
        assert perf.nav_ai == 1.0

@pytest.mark.asyncio
async def test_execute_shadow_trade():
    from backend.app.services.personal_finance_service import execute_shadow_trade, save_portfolio
    from backend.app.agents.personal_finance.models import PortfolioSnapshot, AssetItem
    from backend.app.agents.personal_finance.db_models import ShadowPortfolio, ShadowAsset
    from backend.app.agents.personal_finance.db import engine
    from sqlmodel import Session, select
    
    user_id = "test_user_shadow_trade"
    
    # 1. Setup Initial Portfolio (and Shadow)
    snapshot = PortfolioSnapshot(
        assets=[
            AssetItem(symbol="AAPL", type="Stock", quantity=10, cost_basis=100.0, current_price=100.0)
        ],
        cash_balance=10000.0
    )
    # save_portfolio is async
    await save_portfolio(user_id, snapshot)
    
    # 2. Execute Shadow Trade: BUY 5 AAPL at 120.0
    # Assuming execute_shadow_trade signature: (user_id, symbol, action, quantity, price)
    await execute_shadow_trade(user_id, "AAPL", "BUY", 5, 120.0)
    
    # 3. Verify Shadow Portfolio Updated
    with Session(engine) as session:
        shadow = session.exec(select(ShadowPortfolio).where(ShadowPortfolio.user_id == user_id)).first()
        assert shadow.cash_balance == 10000.0 - (5 * 120.0) # 9400.0
        
        assets = session.exec(select(ShadowAsset).where(ShadowAsset.portfolio_id == shadow.id)).all()
        assert len(assets) == 1
        aapl = assets[0]
        assert aapl.quantity == 15 # 10 + 5
        # Avg cost update: (10*100 + 5*120) / 15 = 1600 / 15 = 106.666...
        assert abs(aapl.avg_cost - 106.67) < 0.1
        
    # 4. Execute Shadow Trade: SELL 5 AAPL at 130.0
    await execute_shadow_trade(user_id, "AAPL", "SELL", 5, 130.0)
    
    # 5. Verify Update
    with Session(engine) as session:
        shadow = session.exec(select(ShadowPortfolio).where(ShadowPortfolio.user_id == user_id)).first()
        assert shadow.cash_balance == 9400.0 + (5 * 130.0) # 10050.0
        
        assets = session.exec(select(ShadowAsset).where(ShadowAsset.portfolio_id == shadow.id)).all()
        aapl = assets[0]
        assert aapl.quantity == 10
