from fastapi import APIRouter
from datetime import datetime
from backend.app.services.market_service import market_service
from backend.infrastructure.utils.json_helpers import clean_nans

router = APIRouter(prefix="/api/macro-data", tags=["Macro Data"])

@router.get("/historical/{indicator}")
async def get_macro_history(indicator: str, period: str = "1y"):
    """Get historical macro data."""
    import asyncio
    result = await asyncio.to_thread(market_service.get_macro_history, indicator, period)
    # Clean NaNs
    result = clean_nans(result)
    
    # Tool already returns formatted response with status/data
    if "error" not in result:
        # Standardize response format if tool didn't include status
        if "status" not in result:
            return {
                "status": "success",
                "data": result.get("data"),
                "indicator": result.get("indicator"),
                "symbol": result.get("symbol"),
                "timestamp": datetime.now().isoformat()
            }
        return result
        
    return {
        "status": "error",
        "message": result.get("error", "Failed to fetch data"),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/fed-implied-probability")
async def get_fed_probability():
    """Get Fed Implied Probability."""
    try:
        import asyncio
        result = await asyncio.to_thread(market_service.get_fed_probability)
        return clean_nans(result)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Server error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
