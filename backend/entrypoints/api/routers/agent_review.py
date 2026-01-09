from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.app.agents.review.agent import run_review_agent
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent/review", tags=["Review Agent"])

class ReviewRequest(BaseModel):
    symbol: str
    user_id: str = "default_user"

async def stream_review(symbol: str, user_id: str):
    """Stream wrapper for review agent"""
    try:
        async for chunk in run_review_agent(symbol, user_id):
            if chunk:
                # Align with frontend format: {"type": "agent_response", "content": "..."}
                msg = {
                    "type": "agent_response",
                    "content": chunk
                }
                yield json.dumps(msg, ensure_ascii=False) + "\n"
    except Exception as e:
        logger.error(f"Review agent failed: {e}")
        yield json.dumps({"type": "error", "content": str(e)}) + "\n"

@router.post("/analyze")
async def start_review(request: ReviewRequest):
    """Starts the Daily Review Agent (Streaming)."""
    return StreamingResponse(
        stream_review(request.symbol, request.user_id),
        media_type="application/x-ndjson"
    )
