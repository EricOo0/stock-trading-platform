from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google_agent.agent import root_agent, APP_NAME, USER_ID, SESSION_ID
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import uvicorn
import asyncio
from dotenv import load_dotenv
import os

# Load env from google_agent/.env
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

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Ensure session exists
        try:
            await session_service.create_session(app_name=APP_NAME, user_id=request.user_id, session_id=request.session_id)
        except Exception as e:
            # Ignore if session already exists
            if "already exists" not in str(e):
                raise e
        
        runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
        
        content = types.Content(role='user', parts=[types.Part(text=request.query)])
        
        async def generate():
            events = runner.run_async(user_id=request.user_id, session_id=request.session_id, new_message=content)
            async for event in events:
                # Yield text from the event if available
                # This depends on the event structure, assuming standard ADK event
                if hasattr(event, 'content') and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            yield part.text

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
