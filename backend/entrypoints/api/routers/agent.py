from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.services.news_sentiment_service import news_sentiment_service

router = APIRouter(prefix="/api/agent/news-sentiment", tags=["News Sentiment Agent"])

class NewsSentimentRequest(BaseModel):
    query: str
    session_id: str

@router.post("/start")
async def start_news_sentiment(request: NewsSentimentRequest):
    """Starts the News Sentiment Agent (Streaming)."""
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        news_sentiment_service.start_research(request.session_id, request.query),
        media_type="application/x-ndjson"
    )
