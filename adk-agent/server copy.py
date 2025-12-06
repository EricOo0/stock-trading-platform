from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google_agent.agent import root_agent, APP_NAME, USER_ID, SESSION_ID
from fintech_agent.agent import fintech_agent # Import Fintech Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import uvicorn
import asyncio
from dotenv import load_dotenv
import os
from tools.registry import Tools

# Initialize the registry once
registry = Tools()

# Load env from google_agent/.env (and maybe root .env logic if needed for tools)
load_dotenv("google_agent/.env")

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize session service globally to persist sessions in memory
session_service = InMemorySessionService()

class ChatRequest(BaseModel):
    query: str
    user_id: str = USER_ID
    session_id: str = SESSION_ID

from fastapi.responses import StreamingResponse

async def run_agent(agent, request: ChatRequest, app_name: str):
    # Ensure session exists
    try:
        await session_service.create_session(app_name=app_name, user_id=request.user_id, session_id=request.session_id)
    except Exception as e:
        if "already exists" not in str(e):
            raise e
    
    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)
    
    content = types.Content(role='user', parts=[types.Part(text=request.query)])
    
    async def generate():
        events = runner.run_async(user_id=request.user_id, session_id=request.session_id, new_message=content)
        async for event in events:
            if hasattr(event, 'content') and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        yield part.text

    return StreamingResponse(generate(), media_type="text/plain")

@app.post("/test/chat")
async def chat(request: ChatRequest):
    try:
        return await run_agent(root_agent, request, APP_NAME)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def fintech_chat(request: ChatRequest):
    try:
        # Use a distinct app_name/session scope or reuse
        return await run_agent(fintech_agent, request, "fintech_agent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
