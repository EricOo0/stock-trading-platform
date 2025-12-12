from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.services.deep_search_service import deep_search_service

router = APIRouter(prefix="/api/agent/deep-search", tags=["Deep Search Agent"])

class DeepSearchRequest(BaseModel):
    query: str
    session_id: str

@router.post("/start")
async def start_deep_search(request: DeepSearchRequest):
    """Starts the Deep Search Agent."""
    return await deep_search_service.start_research(request.session_id, request.query)
