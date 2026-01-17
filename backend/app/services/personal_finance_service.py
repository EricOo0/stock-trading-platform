from typing import List, Dict
import asyncio
from functools import partial
from datetime import datetime
from sqlmodel import Session, select
from backend.app.agents.personal_finance.models import AssetItem, PriceUpdateMap, PriceUpdate, PortfolioSnapshot
from backend.app.agents.personal_finance.db import engine, init_db
from backend.app.agents.personal_finance.db_models import Portfolio, Asset as DBAsset
from backend.infrastructure.market.sina import SinaFinanceTool
from backend.infrastructure.market.akshare_tool import AkShareTool

# Initialize DB tables
init_db()

# Initialize tools
sina_tool = SinaFinanceTool()
ak_tool = AkShareTool()

async def get_portfolio(user_id: str) -> PortfolioSnapshot:
    """
    Retrieve user portfolio from DB.
    """
    with Session(engine) as session:
        statement = select(Portfolio).where(Portfolio.user_id == user_id)
        portfolio = session.exec(statement).first()
        
        if not portfolio:
            # Return empty portfolio
            return PortfolioSnapshot(assets=[], cash_balance=0.0)
            
        assets = []
        for db_asset in portfolio.assets:
            assets.append(AssetItem(
                id=str(db_asset.id),
                symbol=db_asset.symbol,
                name=db_asset.name,
                type=db_asset.type,
                market=db_asset.market,
                quantity=db_asset.quantity,
                cost_basis=db_asset.avg_cost,
                current_price=db_asset.current_price,
                total_value=db_asset.quantity * db_asset.current_price
            ))
            
        return PortfolioSnapshot(assets=assets, cash_balance=portfolio.cash_balance)

async def save_portfolio(user_id: str, snapshot: PortfolioSnapshot) -> PortfolioSnapshot:
    """
    Save/Update user portfolio in DB.
    """
    with Session(engine) as session:
        statement = select(Portfolio).where(Portfolio.user_id == user_id)
        portfolio = session.exec(statement).first()
        
        if not portfolio:
            portfolio = Portfolio(user_id=user_id)
            session.add(portfolio)
        
        portfolio.cash_balance = snapshot.cash_balance
        portfolio.updated_at = datetime.utcnow()
        session.add(portfolio)
        session.commit()
        session.refresh(portfolio) # Get ID
        
        # Simple Strategy: Remove all existing assets and re-add.
        for asset in portfolio.assets:
            session.delete(asset)
            
        new_assets = []
        for item in snapshot.assets:
            db_asset = DBAsset(
                portfolio_id=portfolio.id,
                symbol=item.symbol or "",
                name=item.name or "Unknown",
                type=item.type,
                market=item.market,
                quantity=item.quantity,
                avg_cost=item.cost_basis or 0.0,
                current_price=item.current_price or 0.0
            )
            session.add(db_asset)
            new_assets.append(db_asset)
            
        session.commit()
        
        # Re-construct snapshot to return with new IDs
        result_assets = []
        for db_asset in new_assets:
             # Refresh to get ID
             session.refresh(db_asset)
             result_assets.append(AssetItem(
                id=str(db_asset.id),
                symbol=db_asset.symbol,
                name=db_asset.name,
                type=db_asset.type,
                market=db_asset.market,
                quantity=db_asset.quantity,
                cost_basis=db_asset.avg_cost,
                current_price=db_asset.current_price,
                total_value=db_asset.quantity * db_asset.current_price
            ))
            
        return PortfolioSnapshot(assets=result_assets, cash_balance=portfolio.cash_balance)

async def update_prices(assets: List[AssetItem]) -> PriceUpdateMap:
    """
    Batch update asset prices using Sina (Stock) and AkShare (Fund).
    """
    price_map: Dict[str, PriceUpdate] = {}
    loop = asyncio.get_running_loop()
    
    for asset in assets:
        if not asset.symbol:
            continue
            
        try:
            quote = None
            if asset.type == 'Stock':
                # Map market code if needed.
                market = asset.market or "A-share"
                quote = await loop.run_in_executor(
                    None, 
                    partial(sina_tool.get_stock_quote, symbol=asset.symbol, market=market)
                )
            elif asset.type == 'Fund':
                # AkShare for funds
                # Check if get_fund_nav exists, otherwise try get_stock_quote (ETFs often work there too)
                if hasattr(ak_tool, 'get_fund_nav'):
                    quote = await loop.run_in_executor(
                        None,
                        partial(ak_tool.get_fund_nav, symbol=asset.symbol)
                    )
                else:
                    # Fallback to stock quote if it's an ETF, might work
                    quote = await loop.run_in_executor(
                        None,
                        partial(ak_tool.get_stock_quote, symbol=asset.symbol)
                    )

            if quote and 'current_price' in quote:
                # Sina returns 'current_price', AkShare get_stock_quote returns 'current_price'
                # Handle potential errors in quote dict (e.g. {"error": ...})
                if "error" in quote:
                    print(f"Error updating price for {asset.symbol}: {quote['error']}")
                    continue

                price = float(quote.get('current_price', 0) or 0)
                change_percent = float(quote.get('change_percent', 0) or 0)
                
                # Sina uses 'timestamp', AkShare might differ? 
                # Sina: "timestamp"
                # AkShare: "timestamp"
                
                price_map[asset.symbol] = PriceUpdate(
                    price=price,
                    change_percent=change_percent,
                    update_time=str(quote.get('timestamp', ''))
                )
        except Exception as e:
            # Ignore errors for individual assets to allow partial success
            print(f"Error updating price for {asset.symbol}: {e}")
            continue
            
    return PriceUpdateMap(prices=price_map)
