from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.app.services.news_sentiment_service import news_sentiment_service

# This seems to be an alias or a more specific endpoint for sentiment analysis
router = APIRouter(prefix="/api/agent/sentiment", tags=["Agent - Sentiment"])

class SentimentAnalyzeRequest(BaseModel):
    session_id: str
    query: str

@router.post("/analyze")
async def analyze_sentiment(request: SentimentAnalyzeRequest):
    """
    Stream sentiment analysis.
    """
    return StreamingResponse(
        news_sentiment_service.start_research(request.session_id, request.query),
        media_type="application/x-ndjson"
    )
