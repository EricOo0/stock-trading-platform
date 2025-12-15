from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.services.technical_agent_service import technical_agent_service

router = APIRouter(prefix="/api/agent/technical", tags=["Technical Analysis Agent"])

class AnalysisRequest(BaseModel):
    symbol: str
    session_id: str

@router.post("/analyze")
async def start_analysis(request: AnalysisRequest):
    """Starts the Technical Analysis Agent (Streaming)."""
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        technical_agent_service.start_analysis(request.session_id, request.symbol),
        media_type="application/x-ndjson"
    )
