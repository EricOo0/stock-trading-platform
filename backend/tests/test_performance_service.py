import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlmodel import Session, SQLModel, create_engine, select
from backend.app.agents.personal_finance.db_models import PerformanceHistory, Portfolio, Asset, ShadowPortfolio, ShadowAsset

# Mock Dependencies
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.mark.asyncio
async def test_ensure_performance_history_backfill(session):
    # 1. Setup Data
    user_id = "test_backfill_user"
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=5) # 5 days ago
    
    # Init Portfolio & Shadow (Day -5)
    portfolio = Portfolio(user_id=user_id, cash_balance=5000.0)
    session.add(portfolio)
    shadow_portfolio = ShadowPortfolio(user_id=user_id, cash_balance=5000.0)
    session.add(shadow_portfolio)
    session.commit()
    session.refresh(portfolio)
    session.refresh(shadow_portfolio)
    
    asset = Asset(
        portfolio_id=portfolio.id,
        symbol="AAPL",
        name="Apple Inc.",
        type="Stock",
        quantity=10.0,
        avg_cost=150.0,
        current_price=150.0 # Initial price
    )
    session.add(asset)
    
    shadow_asset = ShadowAsset(
        portfolio_id=shadow_portfolio.id,
        symbol="AAPL",
        quantity=10.0,
        avg_cost=150.0
    )
    session.add(shadow_asset)
    
    # Create INITIAL Performance Record at Day -5
    # Assuming initial NAV is 1.0
    init_perf = PerformanceHistory(
        user_id=user_id,
        date=start_date.strftime("%Y-%m-%d"),
        nav_user=1.0, nav_ai=1.0, nav_sh=1.0, nav_sz=1.0,
        total_assets_user=6500.0, # 5000 + 10*150
        total_assets_ai=6500.0
    )
    session.add(init_perf)
    session.commit()
    
    # 2. Mock Market Data Fetcher
    # Should return prices for Day -5 (last record) to Today (Day 0)
    # Range of i should be 0 to 5.
    
    dates_to_fetch = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6)]
    
    mock_market_data = {}
    for i, date_str in enumerate(dates_to_fetch):
        # AAPL price: 150 * (1.1)^(i) 
        # Day -5 (i=0): 150 * 1.0 = 150.0
        # Day -4 (i=1): 150 * 1.1 = 165.0
        price = 150.0 * (1.1 ** i)
        mock_market_data[date_str] = {
            "AAPL": price,
            "000001.SS": 3000.0 * (1.01 ** i), # Mock index
            "399001.SZ": 10000.0 * (1.01 ** i) # Mock index
        }
        
    # We need to mock fetch_market_history. 
    # It likely takes a list of dates and list of symbols.
    # We will implement it to return the map above.
    
    with patch("backend.app.agents.personal_finance.performance_service.fetch_market_history_batch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_market_data
        
        # 3. Call Service
        # Note: We haven't created the service yet, so this import will fail, which is expected for TDD
        try:
            from backend.app.agents.personal_finance.performance_service import ensure_performance_history
            
            # This function should backfill Day -4 to Day 0 (Today)
            await ensure_performance_history(user_id, session=session)
            
            # 4. Verify DB
            history = session.exec(select(PerformanceHistory).where(PerformanceHistory.user_id == user_id).order_by(PerformanceHistory.date)).all()
            
            # Expect 6 records: Day -5 (initial) + 5 generated days
            assert len(history) == 6 
            
            # Check continuity
            dates = [h.date for h in history]
            expected_dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6)]
            assert dates == expected_dates
            
            # Check NAV growth (roughly)
            # Last day AAPL price is 150 * 1.1^5 ~ 241.5
            # Cash 5000 constant
            # Total Asset = 5000 + 10 * 241.5 = 7415
            # Initial Asset = 6500
            # NAV should be around 7415 / 6500 = 1.14
            last_record = history[-1]
            assert last_record.total_assets_user > 6500.0
            assert last_record.nav_user > 1.0
            
        except ImportError:
            pytest.fail("Module backend.app.agents.personal_finance.performance_service not found")
