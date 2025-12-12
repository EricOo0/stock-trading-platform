from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
from datetime import datetime
from backend.app.services.simulation_service import SimulationService
from backend.app.services.fintech_service import fintech_service
from backend.app.registry import Tools

router = APIRouter(prefix="/api/simulation", tags=["Simulation"])

# Initialize Service
simulation_service = SimulationService()
tools = Tools()

@router.get("/tasks")
async def get_tasks():
    """Get all simulation tasks."""
    return {"status": "success", "data": simulation_service.get_all_tasks()}

@router.get("/task/{task_id}")
async def get_task(task_id: str):
    """Get a specific simulation task."""
    task = simulation_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "data": task}

@router.post("/create")
async def create_task(payload: Dict[str, Any] = Body(...)):
    """Create a new simulation task."""
    symbol = payload.get("symbol")
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol required")
    task = simulation_service.create_task(symbol)
    return {"status": "success", "data": task}

@router.post("/run")
async def run_simulation(payload: Dict[str, Any] = Body(...)):
    """Run a simulation step."""
    task_id = payload.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="Task ID required")
    
    try:
        # tools is passed to service method
        # Direct async call (No longer blocking)
        result = await simulation_service.run_daily_simulation(task_id, tools)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def simulation_chat(payload: Dict[str, Any] = Body(...)):
    """
    Dedicated chat endpoint for Simulation Service.
    It proxies the request to the Fintech Agent (Chairman) but formatted for simulation needs.
    """
    query = payload.get("query")
    session_id = payload.get("session_id", "sim_default")
    user_id = "simulation_system"
    
    if not query:
        raise HTTPException(status_code=400, detail="Query required")

    # Reuse Fintech Service's chat_stream
    return StreamingResponse(
        fintech_service.chat_stream(query, user_id, session_id),
        media_type="application/x-ndjson"
    )
