from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.infrastructure.browser.session_manager import session_manager

router = APIRouter(prefix="/api/browser", tags=["Browser"])

class SessionCreateRequest(BaseModel):
    user_id: Optional[str] = None

@router.post("/session")
async def create_browser_session(request: SessionCreateRequest):
    """Creates a new Steel browser session."""
    session = session_manager.create_session()
    if session:
        return {"status": "success", "data": session}
    else:
        raise HTTPException(status_code=500, detail="Failed to create session")

@router.get("/session/{session_id}/view")
async def view_browser_session(session_id: str):
    """Redirects to the Steel session viewer."""
    # Construct the viewer URL. 
    # Logic taken from steel_browser.py
    viewer_url = f"https://app.steel.dev/sessions/{session_id}"
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=viewer_url)
