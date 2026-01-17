import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from sqlmodel import Session, select
from backend.app.agents.personal_finance.db_models import (
    PerformanceHistory, Portfolio, ShadowPortfolio, Asset, ShadowAsset
)

logger = logging.getLogger(__name__)

async def fetch_market_history_batch(dates: List[str], symbols: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Fetches historical close prices for a batch of dates and symbols.
    Returns: { "YYYY-MM-DD": { "SYMBOL": price, ... }, ... }
    
    This function should be mocked in tests or implemented with a real data provider.
    """
    raise NotImplementedError("fetch_market_history_batch is not implemented yet")

def calculate_portfolio_value(
    cash: float, 
    assets: List[Asset] | List[ShadowAsset], 
    prices: Dict[str, float]
) -> float:
    total = cash
    for asset in assets:
        price = prices.get(asset.symbol)
        if price is None:
            # Fallback: if price is missing, use 0.0 or handle error. 
            # In a real system, we might carry forward previous price.
            # For now, warn and use 0.0 to avoid crashing, but this affects NAV.
            # Ideally, prices dict should be complete.
            price = 0.0
        total += asset.quantity * price
    return total

async def ensure_performance_history(user_id: str, session: Session):
    """
    Ensures that PerformanceHistory records exist from the last recorded date up to Today.
    Fills gaps using 'Lazy Backfill' strategy:
    - Assumes the CURRENT portfolio holdings were held constant throughout the gap.
    - Uses Chain Linking method for NAV: NAV_t = NAV_{t-1} * (Value_t / Value_{t-1})
      where Value_t and Value_{t-1} are calculated using CURRENT holdings.
    """
    
    # 1. Get the latest performance record
    stmt = select(PerformanceHistory).where(PerformanceHistory.user_id == user_id).order_by(PerformanceHistory.date.desc())
    latest_record = session.exec(stmt).first()
    
    today = datetime.utcnow().date()
    
    if not latest_record:
        logger.warning(f"No performance history found for user {user_id}. Cannot backfill.")
        return

    last_date = datetime.strptime(latest_record.date, "%Y-%m-%d").date()
    
    if last_date >= today:
        logger.debug(f"Performance history for user {user_id} is up to date ({last_date}).")
        return

    # 2. Identify gap
    # We need to fill from (last_date + 1) to today.
    # To calculate return for (last_date + 1), we need prices for last_date AND (last_date + 1).
    dates_to_fill = []
    curr = last_date + timedelta(days=1)
    while curr <= today:
        dates_to_fill.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)
        
    logger.info(f"Backfilling {len(dates_to_fill)} days for user {user_id} from {dates_to_fill[0]} to {dates_to_fill[-1]}")

    # 3. Get Portfolio Snapshot (Current)
    portfolio = session.exec(select(Portfolio).where(Portfolio.user_id == user_id)).first()
    shadow_portfolio = session.exec(select(ShadowPortfolio).where(ShadowPortfolio.user_id == user_id)).first()
    
    if not portfolio or not shadow_portfolio:
        logger.error(f"Portfolio or ShadowPortfolio missing for user {user_id}")
        return

    user_assets = session.exec(select(Asset).where(Asset.portfolio_id == portfolio.id)).all()
    shadow_assets = session.exec(select(ShadowAsset).where(ShadowAsset.portfolio_id == shadow_portfolio.id)).all()
    
    # Collect symbols
    symbols: Set[str] = set()
    for a in user_assets:
        symbols.add(a.symbol)
    for a in shadow_assets:
        symbols.add(a.symbol)
        
    benchmarks = ["000001.SS", "399001.SZ"] 
    for b in benchmarks:
        symbols.add(b)
        
    symbol_list = list(symbols)
    
    # 4. Fetch Market Data
    # We need prices for ALL dates in [last_date] + dates_to_fill
    dates_to_fetch = [latest_record.date] + dates_to_fill
    
    try:
        market_data = await fetch_market_history_batch(dates_to_fetch, symbol_list)
    except NotImplementedError:
        # Re-raise if not mocked/implemented
        raise

    # 5. Iterate and Calculate
    # We maintain running NAVs
    current_nav_user = latest_record.nav_user
    current_nav_ai = latest_record.nav_ai
    current_nav_sh = latest_record.nav_sh
    current_nav_sz = latest_record.nav_sz
    
    # Loop from first missing day
    # previous_date_str starts as latest_record.date
    prev_date_str = latest_record.date
    
    for date_str in dates_to_fill:
        # Prices for Today and Yesterday
        prices_curr = market_data.get(date_str, {})
        prices_prev = market_data.get(prev_date_str, {})
        
        # --- User Portfolio ---
        val_curr_user = calculate_portfolio_value(portfolio.cash_balance, user_assets, prices_curr)
        val_prev_user = calculate_portfolio_value(portfolio.cash_balance, user_assets, prices_prev)
        
        if val_prev_user > 0:
            return_user = (val_curr_user - val_prev_user) / val_prev_user
        else:
            return_user = 0.0
            
        current_nav_user = current_nav_user * (1 + return_user)
        
        # --- AI Portfolio ---
        val_curr_ai = calculate_portfolio_value(shadow_portfolio.cash_balance, shadow_assets, prices_curr)
        val_prev_ai = calculate_portfolio_value(shadow_portfolio.cash_balance, shadow_assets, prices_prev)
        
        if val_prev_ai > 0:
            return_ai = (val_curr_ai - val_prev_ai) / val_prev_ai
        else:
            return_ai = 0.0
            
        current_nav_ai = current_nav_ai * (1 + return_ai)
        
        # --- Benchmarks ---
        # Assuming simple price return for benchmarks
        # SH
        sh_curr = prices_curr.get("000001.SS", 0.0)
        sh_prev = prices_prev.get("000001.SS", 0.0)
        if sh_prev > 0 and sh_curr > 0:
            current_nav_sh = current_nav_sh * (sh_curr / sh_prev)
            
        # SZ
        sz_curr = prices_curr.get("399001.SZ", 0.0)
        sz_prev = prices_prev.get("399001.SZ", 0.0)
        if sz_prev > 0 and sz_curr > 0:
            current_nav_sz = current_nav_sz * (sz_curr / sz_prev)
            
        # Create Record
        new_record = PerformanceHistory(
            user_id=user_id,
            date=date_str,
            nav_user=current_nav_user,
            nav_ai=current_nav_ai,
            nav_sh=current_nav_sh,
            nav_sz=current_nav_sz,
            total_assets_user=val_curr_user,
            total_assets_ai=val_curr_ai
        )
        session.add(new_record)
        
        # Move forward
        prev_date_str = date_str
        
    session.commit()
    logger.info("Backfill complete.")
