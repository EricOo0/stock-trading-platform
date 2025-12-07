from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import uvicorn
import os
import json
import asyncio
import warnings

# Suppress Pydantic serialization warnings from google-genai when using custom LLM
warnings.filterwarnings("ignore", message=".*Pydantic serializer warnings.*")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.main")

# Import the Chairman Agent
from agents.chairman import chairman_agent

app = FastAPI(title="Fintech Multi-Agent Receptionist")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session Service
session_service = InMemorySessionService()

class ChatRequest(BaseModel):
    query: str
    user_id: str = "user_default"
    session_id: str = "session_default"

async def event_generator(runner, user_id, session_id, content):
    """
    Streams events in a JSON-based Data Bus protocol.
    """
    events = runner.run_async(user_id=user_id, session_id=session_id, new_message=content)
    async for event in events:
        try:
            # 1. Handle Thoughts / Text Content
            if hasattr(event, 'content') and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        # Determine if this is a final answer or intermediate thought
                        # ADK often interleaves them. 
                        # We'll treat all text as 'answer' chunks for now, 
                        # unless we can distinguish 'thought' (reasoning) from 'response'.
                        # Frontend often treats 'answer' as the main display.
                        
                        # Note: If the agent is in a "reasoning" step, this might be a thought.
                        # But without explicit event types for 'Reasoning', we assume text is output.
                        # However, for Multi-Agent, intermediate steps are critical.
                        
                        # Simplification: Stream as 'chunk'
                        message = {
                            "type": "chunk", 
                            "content": part.text
                        }
                        yield json.dumps(message, ensure_ascii=False) + "\n"
            
            # 2. Handle Tool Calls (The "Process" Data)
            # Check for tool usage events. ADK might expose this via specific event attributes.
            # Hypothetically checking for 'tool_use' or similar in event
            # Since strict types aren't visible, we check attributes dynamically.
            
            # If event represents a step where a tool is called:
            if hasattr(event, 'tool_calls') and event.tool_calls:
                 for tool_call in event.tool_calls:
                     message = {
                         "type": "thought",
                         "content": f"Use {tool_call.function.name}({tool_call.function.arguments})"
                     }
                     yield json.dumps(message, ensure_ascii=False) + "\n"

            # 3. Handle Tool Outputs
            if hasattr(event, 'tool_outputs') and event.tool_outputs:
                for tool_output in event.tool_outputs:
                     # This might be voluminous, maybe truncate
                     truncated_output = str(tool_output.tool_response)[:200] + "..."
                     message = {
                         "type": "thought",
                         "content": f"Observation: {truncated_output}"
                     }
                     yield json.dumps(message, ensure_ascii=False) + "\n"

        except Exception as e:
            print(f"Error processing event: {e}")
            continue

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        app_name = "fintech_chairman"
        
        # Create session if needed
        try:
            await session_service.create_session(app_name=app_name, user_id=request.user_id, session_id=request.session_id)
        except Exception as e:
            if "already exists" not in str(e):
                pass

        runner = Runner(agent=chairman_agent, app_name=app_name, session_service=session_service)
        content = types.Content(role='user', parts=[types.Part(text=request.query)])
        
        return StreamingResponse(
            event_generator(runner, request.user_id, request.session_id, content),
            media_type="application/x-ndjson"
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def start():
    """
    Entry point for running the server programmatically.
    Note: Environment configuration is done in main.py before this module is imported.
    """
    uvicorn.run(app, host="0.0.0.0", port=9000)


