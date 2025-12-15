from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.app.services.macro_agent_service import macro_agent_service

router = APIRouter(prefix="/api/agent/macro", tags=["Agent - Macro"])

class MacroAnalyzeRequest(BaseModel):
    session_id: str

@router.post("/analyze")
async def analyze_macro(request: MacroAnalyzeRequest):
    """
    Stream macro economic analysis.
    """
    return StreamingResponse(
        macro_agent_service.analyze_stream(request.session_id),
        media_type="application/x-ndjson"
    )
