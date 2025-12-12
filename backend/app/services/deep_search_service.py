import logging
import uuid
from typing import Dict, Any, Optional

from google.adk.runners import Runner
from google.adk.apps.app import App
from google.adk.sessions import InMemorySessionService
from google.genai import types

from backend.app.agents.deep_search.agent import deep_search_agent
from backend.infrastructure.browser.steel_browser import browser_engine

logger = logging.getLogger(__name__)

class DeepSearchService:
    def __init__(self):
        # Initialize Runner with InMemorySessionService
        self.session_service = InMemorySessionService()
        self.app = App(
            name="deep_search_app",
            root_agent=deep_search_agent
        )
        self.runner = Runner(app=self.app, session_service=self.session_service)

    async def start_research(self, session_id: str, query: str) -> Dict[str, Any]:
        """
        Starts the Deep Search Agent attached to a specific browser session.
        """
        try:
            logger.info(f"Starting Deep Search for session {session_id} with query: {query}")
            
            # 1. Attach Browser Engine to Session
            # This ensures the 'visit_page' tool uses the correct session.
            # Only if session_id is provided.
            if session_id:
                await browser_engine.initialize_session(session_id=session_id)
            
            # 2. Run Agent
            # Using a simplified synchronous-like run for now, but ADK is async.
            # Runner.run_agent takes inputs.
            
            # ADK inputs need to be properly formatted?
            # runner.run_agent(agent_name, inputs, session_id=?)
            # Wait, runner.run_agent_async?
            
            # Reusing logic from old api_server.py: 
            # runner.run_agent_async(agent_name="deep_search_agent", input=Content(...), session_id=session_id)
            
            # Create a unique session ID for the ADK conversation (different from browser session_id? or same?)
            # Ideally same for traceability, but ADK handles session persistence.
            # Let's use the browser session_id as the ADK session_id if possible.
            adk_session_id = session_id or str(uuid.uuid4())
            
            input_content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=query)]
            )
            
            # Run the agent
            # We catch the result. For MVP we don't stream here yet, just wait.
            result = await self.runner.run_agent_async(
                agent_name="deep_search_agent",
                input=input_content,
                session_id=adk_session_id
            )
            
            # Extract final response from session state or result
            # The agent doesn't have a specific output_key set in agent.py
            # So we might check the last message or state.
            
            # For now, return success status.
            return {
                "status": "success",
                "session_id": session_id,
                "adk_session_id": adk_session_id,
                "data": "Agent started/finished (Sync mode limited, check logs)"
            }

        except Exception as e:
            logger.error(f"Deep Search Service failed: {e}")
            return {"status": "error", "message": str(e)}

deep_search_service = DeepSearchService()
