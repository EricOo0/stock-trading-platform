from fastapi import APIRouter, Body
from typing import Dict, Any
from datetime import datetime
from backend.app.registry import Tools
from backend.infrastructure.utils.json_helpers import clean_nans

router = APIRouter(tags=["Financial Report"])
tools = Tools()

@router.get("/api/financial-report/{symbol}")
async def get_financial_report(symbol: str):
    """Get financial report metadata and metrics."""
    import asyncio
    
    # Run blocking I/O in thread pool
    metrics_task = asyncio.to_thread(tools.get_financial_metrics, symbol)
    report_task = asyncio.to_thread(tools.get_company_report, symbol)
    
    # Parallel execution
    metrics_result, report_result = await asyncio.gather(metrics_task, report_task)
    
    metrics_array = []
    if metrics_result.get("status") == "success":
        metrics_array = metrics_result.get("metrics", [])

    response = {
        'status': 'success',
        'symbol': symbol,
        'metrics': metrics_array,
        'latest_report': report_result if report_result.get('status') in ['success', 'partial'] else None,
        'timestamp': datetime.now().isoformat()
    }
    return clean_nans(response)

@router.get("/api/financial-report/analyze/{symbol}")
async def analyze_financial_report(symbol: str):
    """Analyze financial report."""
    import asyncio
    # Blocking analysis
    result = await asyncio.to_thread(tools.analyze_report, symbol)
    return clean_nans(result)

@router.post("/api/tools/financial_report_tool/get_financial_indicators")
async def get_financial_indicators_post(payload: Dict[str, Any] = Body(...)):
    """Get financial indicators POST."""
    symbol = payload.get("symbol")
    years = payload.get("years", 3)
    
    if not symbol:
        return {"status": "error", "message": "Symbol required"}
        
    import asyncio
    # Blocking fetch
    indicators_data = await asyncio.to_thread(tools.get_financial_indicators, symbol, years=years)
    market = tools._detect_market(symbol)
    
    response = {
        'status': 'success',
        'symbol': symbol,
        'market': market,
        'data_source': 'registry',
        'indicators': indicators_data,
        'timestamp': datetime.now().isoformat()
    }
    return clean_nans(response)
