from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, Dict, Any
from datetime import datetime
from backend.app.services.market_service import market_service
from backend.infrastructure.utils.json_helpers import clean_nans
from backend.app.registry import Tools

router = APIRouter(prefix="/api/market", tags=["Market Data"])
tools = Tools() # Helper for batch

@router.post("/price")
async def get_price(payload: dict):
    """Get real-time price."""
    symbol = payload.get("symbol")
    market = payload.get("market")
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")
    
    import asyncio
    return clean_nans(await asyncio.to_thread(market_service.get_stock_price, symbol, market))

@router.get("/metrics/{symbol}")
async def get_metrics(symbol: str):
    """Get financial metrics."""
    import asyncio
    return clean_nans(await asyncio.to_thread(market_service.get_financial_metrics, symbol))

@router.get("/indicators/{symbol}")
async def get_indicators(symbol: str):
    """Get financial indicators."""
    import asyncio
    return clean_nans(await asyncio.to_thread(market_service.get_financial_indicators, symbol))

@router.get("/historical/{symbol}")
async def get_historical(symbol: str, period: str = "30d", interval: str = "1d"):
    """Get historical data."""
    import asyncio
    return clean_nans(await asyncio.to_thread(market_service.get_historical_data, symbol, period, interval))

@router.get("/technical/{symbol}")
async def get_technical(symbol: str, period: str = "1y"):
    """Get technical indicators (Historical Series)."""
    import asyncio
    results = await asyncio.to_thread(market_service.get_technical_history, symbol, period)
    
    return clean_nans({
        "status": "success",
        "symbol": symbol,
        "data": results,
        "timestamp": datetime.now().isoformat()
    })

@router.get("/macro")
async def get_macro(query: str):
    """Get macro data."""
    import asyncio
    return clean_nans(await asyncio.to_thread(market_service.get_macro_data, query))

# --- Batch & Hot (Legacy Compat) ---

@router.get("-data/hot") # /api/market-data/hot
async def get_hot_stocks():
    """Get hot stocks."""
    import asyncio
    results = await asyncio.to_thread(market_service.get_hot_stocks)
    response = {
        "status": "success",
        "data": results,
        "timestamp": datetime.now().isoformat(),
        "count": len(results)
    }
    return clean_nans(response)

@router.post("-data") # /api/market-data
async def query_market_data(payload: Dict[str, Any] = Body(...)):
    """Batch query market data (Parallellized)."""
    query = payload.get("query", "")
    symbols = tools.extract_symbols(query)
    
    if not symbols:
        return {
            'status': 'error',
            'symbol': query,
            'message': 'No symbols identified',
            'timestamp': datetime.now().isoformat(),
            'data_source': 'real'
        }

    import asyncio
    
    # Define async wrapper for parallel execution
    async def fetch_price(sym):
        try:
            res = await asyncio.to_thread(tools.get_stock_price, sym)
            if res and "error" not in res:
                return {
                 "status": "success",
                 "symbol": sym,
                 "data": res,
                 "timestamp": datetime.now().isoformat(),
                 "cache_hit": False,
                 "response_time_ms": 0
             }
            else:
                return {
                 "status": "error",
                 "symbol": sym,
                 "error_message": res.get("error", "Query failed") if res else "Query failed"
             }
        except Exception as e:
             return {
                 "status": "error",
                 "symbol": sym,
                 "error_message": str(e)
             }

    # Execute all fetches in parallel
    results = await asyncio.gather(*(fetch_price(sym) for sym in symbols))
    
    if len(results) == 1:
        first = results[0]
        if first["status"] == "success":
            response = {
                'status': 'success',
                'symbol': first['symbol'],
                'data': first['data'],
                'timestamp': datetime.now().isoformat(),
                'data_source': 'real',
                'cache_hit': False,
                'response_time_ms': 0
            }
        else:
             response = {
                'status': 'error',
                'symbol': first['symbol'],
                'message': first.get('error_message'),
                'timestamp': datetime.now().isoformat(),
                'data_source': 'real'
            }
    else:
        success_count = sum(1 for r in results if r["status"] == "success")
        response = {
            'status': 'success' if success_count == len(results) else 'partial',
            'results': results,
            'timestamp': datetime.now().isoformat(),
            'data_source': 'real'
        }
    return clean_nans(response)
