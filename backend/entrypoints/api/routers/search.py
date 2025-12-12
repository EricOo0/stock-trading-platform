from fastapi import APIRouter, Query
from datetime import datetime
from backend.app.registry import Tools

router = APIRouter(prefix="/api", tags=["Search"])
tools = Tools()

@router.get("/web-search")
async def web_search(q: str = Query(..., description="Search query")):
    """Web Search."""
    import asyncio
    results = await asyncio.to_thread(tools.search_market_news, q, provider='auto')
    if results:
        return {
            'status': 'success',
            'query': q,
            'results': results,
            'provider': 'auto',
            'timestamp': datetime.now().isoformat()
        }
    return {
        'status': 'error',
        'message': 'Search failed or no results',
        'timestamp': datetime.now().isoformat()
    }
