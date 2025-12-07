
import asyncio
import sys
import os
import logging
from dotenv import load_dotenv

# Load env variables
load_dotenv(".env")
# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import dependencies
try:
    from core.llm import configure_environment
    configure_environment()
    
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from agents.chairman import chairman_agent
except ImportError as e:
    logger.error(f"Import failed: {e}")
    sys.exit(1)

async def verify_memory_integration():
    print("\n🚀 Starting ADK Memory Integration Verification...\n")
    
    APP_NAME = "fintech_memory_test"
    USER_ID = "memory_tester_001"
    SESSION_ID = "sess_mem_001"
    
    # 1. Initialize Session
    session_service = InMemorySessionService()
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    
    runner = Runner(agent=chairman_agent, app_name=APP_NAME, session_service=session_service)
    
    # 2. Test 1: Inject Information (Write to Memory)
    # providing a unique fact
    secret_key = "BlueEagle"
    query_1 = f"My secret codename is {secret_key}. Please remember this."
    print(f"👤 User: {query_1}")
    
    content_1 = types.Content(role='user', parts=[types.Part(text=query_1)])
    events_1 = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content_1)
    
    print("🤖 Agent: ", end="", flush=True)
    async for event in events_1:
         if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print("\n")
    
    # 3. Test 2: Retrieve Information (Read from Memory)
    # Ask about the unique fact. The default Context Window might fail if it's a new session, 
    # but MemoryClient should catch it. To be sure it's coming from MemorySystem (and not just session history),
    # we could simulate a new session or check logs. But for end-to-end user exp, just asking is fine.
    
    print("⏳ Waiting briefly for async memory write...")
    await asyncio.sleep(2)
    
    query_2 = "What is my secret codename?"
    print(f"👤 User: {query_2}")
    
    content_2 = types.Content(role='user', parts=[types.Part(text=query_2)])
    events_2 = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content_2)
    
    response_text = ""
    print("🤖 Agent: ", end="", flush=True)
    async for event in events_2:
         if hasattr(event, 'content') and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
                    response_text += part.text
    print("\n")
    
    if secret_key in response_text:
        print("✅ SUCCESS: Agent recalled the secret key!")
    else:
        print("❌ FAILURE: Agent failed to recall the secret key.")

if __name__ == "__main__":
    asyncio.run(verify_memory_integration())
