from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.encoders import jsonable_encoder
from typing import Dict, Any, List
import math
from sse_starlette.sse import EventSourceResponse
from backend.app.services.research.job_manager import JobManager
from backend.app.services.research.stream_manager import stream_manager
from backend.infrastructure.database.models.research import ResearchJob
from backend.app.agents.research.research_agent import run_agent

router = APIRouter(prefix="/api/research", tags=["Research"])
job_manager = JobManager()


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively replace NaN and Infinity with None to ensure JSON compliance.
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    return obj


@router.post("/start")
async def start_research(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Start a new Deep Research job.
    """
    query = payload.get("query")
    user_id = "default_user"  # TODO: Get from auth

    if not query:
        raise HTTPException(status_code=400, detail="Query required")

    job = job_manager.create_job(user_id, query)

    # Notify listeners that job is starting
    await stream_manager.push_event(job.id, "status", "starting")

    # Trigger Agent in Background
    background_tasks.add_task(run_agent, job.id, query)

    return {"status": "created", "job_id": job.id}


@router.get("/{job_id}/stream")
async def stream_job(job_id: str, request: Request):
    """
    SSE Stream for job updates.
    """
    return EventSourceResponse(stream_manager.connect(job_id))


@router.get("/history")
async def get_history(limit: int = 20):
    """
    Get history of research jobs.
    """
    user_id = "default_user"  # TODO
    jobs = job_manager.list_jobs(user_id, limit)
    return {"status": "success", "data": jobs}


@router.get("/{job_id}/state")
async def get_job_state(job_id: str):
    """
    Get full state of a job (details + events + artifacts) for restoration.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    events = job_manager.get_events(job_id)
    artifacts = job_manager.get_artifacts(job_id)

    # Merge artifacts into events for history restoration (Backward Compatibility)
    # Convert SQLModel objects to dicts or compatible objects

    # We want a unified list sorted by timestamp
    unified_history = []

    # Add regular events
    for e in events:
        unified_history.append({
            "type": e.type,
            "payload": e.payload,
            "created_at": e.timestamp.isoformat() if e.timestamp else None
        })

    # Add artifacts as 'artifact' events
    for a in artifacts:
        # Check if this artifact is already in events (to avoid duplication for new jobs)
        # New jobs save artifact events explicitly. We can check by timestamp rough match or just assume
        # duplication isn't fatal (UI might show double, but let's try to dedup based on type/title?)
        # Simply: If we implemented double-write recently, old jobs won't have it.
        # Let's rely on the fact that 'events' from DB might not contain 'artifact' type for old jobs.

        # Simple heuristic: If events list does NOT contain an event with type='artifact' and same title, add it.
        already_exists = any(
            e.type == 'artifact' and
            isinstance(e.payload, dict) and
            e.payload.get('title') == a.title
            for e in events
        )

        if not already_exists:
            unified_history.append({
                "type": "artifact",
                "payload": {
                    "type": a.type,
                    "title": a.title,
                    "data": a.data
                },
                "created_at": a.created_at.isoformat() if a.created_at else None
            })

    # Sort by created_at
    unified_history.sort(key=lambda x: x['created_at'] or "")

    response_data = {
        "status": "success",
        "job": job,
        "events": unified_history
    }
    
    # Ensure all data is JSON compliant (handle NaN/Infinity)
    return sanitize_for_json(jsonable_encoder(response_data))


@router.post("/{job_id}/remark")
async def add_remark(job_id: str, payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    User adds a remark/feedback to the running job.
    If the job was completed or failed, this triggers a new run (multi-turn).
    """
    remark = payload.get("remark")
    if not remark:
        raise HTTPException(status_code=400, detail="Remark content required")

    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Log user remark as an event
    event = job_manager.append_event(
        job_id, "user_remark", {"content": remark})

    import json
    # Push to StreamManager to notify Agent (if listening) or Client
    await stream_manager.push_event(job_id, "user_remark", json.dumps({"content": remark}))

    # Multi-turn Logic:
    # If job is finished, restart it with the new remark as input
    if job.status in ["completed", "failed"]:
        # Update status to running PERSISTENTLY
        job_manager.update_job_status(job.id, "running")

        # Trigger background run
        # Pass the remark as the "new query" effectively
        import asyncio
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Triggering run_agent for multi-turn remark. Job: {job.id}")

        # Explicitly schedule using asyncio to ensure it runs independently of request scope
        # (BackgroundTasks is also fine, but asyncio.create_task is more 'explicit' per user request for debugging)
        asyncio.create_task(run_agent(job.id, remark))

        # Push status update to frontend immediately
        await stream_manager.push_event(job.id, "status", "running")

    return {"status": "success", "event_id": event.id}
