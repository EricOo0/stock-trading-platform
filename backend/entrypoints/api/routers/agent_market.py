from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.app.services.market_agent_service import market_agent_service

router = APIRouter(prefix="/api/agent/market", tags=["Agent Market"])

@router.post("/outlook")
async def analyze_market_outlook():
    """
    Stream market outlook analysis based on sector flows.
    """
    return StreamingResponse(
        market_agent_service.analyze_outlook_stream(),
        media_type="text/event-stream"
    )
