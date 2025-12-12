from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.app.services.fintech_service import fintech_service

router = APIRouter(tags=["Fintech Agent"])

class ChatRequest(BaseModel):
    query: str
    user_id: str = "user_default"
    session_id: str = "session_default"

@router.post("/chat")
async def chat(request: ChatRequest):
    """Streaming chat endpoint for Fintech Agent."""
    return StreamingResponse(
        fintech_service.chat_stream(request.query, request.user_id, request.session_id),
        media_type="application/x-ndjson"
    )
