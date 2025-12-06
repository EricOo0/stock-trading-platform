
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load env variables (GOOGLE_API_KEY)
load_dotenv("fintech_agent/.env")

# Ensure project root is in path to import tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import the agent to test
from fintech_agent.agent import fintech_agent

async def test_agent():
    print("--- Testing Fintech Agent ---")
    
    APP_NAME = "fintech_test"
    USER_ID = "test_user"
    SESSION_ID = "test_session"
    
    session_service = InMemorySessionService()
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    
    runner = Runner(agent=fintech_agent, app_name=APP_NAME, session_service=session_service)
    
    # Test Query 1: Stock Price (Simple tool call)
    query = "What is the current price of AAPL?"
    print(f"\nUser: {query}")
    content = types.Content(role='user', parts=[types.Part(text=query)])
    
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)
    
    print("Agent: ", end="", flush=True)
    async for event in events:
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print("\n")

    # Test Query 2: Search (Search tool call)
    query = "Find latest news about Tesla."
    print(f"\nUser: {query}")
    content = types.Content(role='user', parts=[types.Part(text=query)])
    
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)
    
    print("Agent: ", end="", flush=True)
    async for event in events:
        if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    asyncio.run(test_agent())
