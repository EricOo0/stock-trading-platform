from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.app.services.fintech_service import fintech_service

router = APIRouter(prefix="/api/agent/financial", tags=["Agent - Financial"])

class FinancialAnalyzeRequest(BaseModel):
    session_id: str
    query: str
    user_id: str = "guest"

@router.post("/chat")
async def chat_financial(request: FinancialAnalyzeRequest):
    """
    Stream financial analysis chat.
    """
    return StreamingResponse(
        fintech_service.chat_stream(request.query, request.user_id, request.session_id),
        media_type="application/x-ndjson"
    )
