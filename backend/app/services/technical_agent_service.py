import asyncio
import logging
import uuid
import json
from typing import AsyncGenerator
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from backend.app.agents.technical_analysis.agent import create_technical_analysis_agent
from backend.app.agents.technical_analysis.callbacks import TechnicalAnalysisCallbackHandler
from backend.app.registry import Tools

logger = logging.getLogger(__name__)

class TechnicalAgentService:
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.tools = Tools()

    async def start_analysis(self, session_id: str, symbol: str) -> AsyncGenerator[str, None]:
        """
        Starts the Technical Analysis Agent and yields events.
        """
        logger.info(f"Starting technical analysis for {symbol} (Session: {session_id})")
        
        # 1. Setup
        adk_session_id = session_id or str(uuid.uuid4())
        user_id = "technical_analyst_user"
        
        # 2. Fetch Data (Direct assembly as requested)
        try:
            # 2. Fetch Data (Direct assembly as requested)
            context = self.tools.get_technical_context(symbol)
            context_json = json.dumps(context, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to fetch context: {e}")
            yield json.dumps({"type": "error", "content": f"Data fetch failed: {str(e)}"}) + "\n"
            return

        # 3. Create Agent (No tools needed now)
        # Pass handler for debug logging
        handler = TechnicalAnalysisCallbackHandler()
        agent = create_technical_analysis_agent(handler=handler)

        try:
             await self.session_service.create_session(
                app_name="technical_analysis_app",
                user_id=user_id,
                session_id=adk_session_id
            )
        except Exception:
            pass 
            
        try:
            runner = Runner(
                agent=agent,
                app_name="technical_analysis_app",
                session_service=self.session_service
            )
            
            # 4. Construct Prompt with Injected Data
            prompt_text = f"""
Analyze the technical status of {symbol} (Symbol Code: {symbol}).

### Technical Data Context
```json
{context_json}
```

Please provide your analysis based on the above data.
"""
            input_content = types.Content(role="user", parts=[types.Part(text=prompt_text)])
            
            # 5. Run Agent
            events = runner.run_async(
                user_id=user_id, 
                session_id=adk_session_id, 
                new_message=input_content
            )
            
            async for event in events:
                try:
                    if hasattr(event, 'content') and event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                message = {
                                    "type": "agent_response", 
                                    "content": part.text
                                }
                                yield json.dumps(message, ensure_ascii=False) + "\n"
                            
                except Exception as e:
                    logger.warning(f"Error parsing event: {e}")

        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            yield json.dumps({
                "type": "error",
                "content": str(e)
            }) + "\n"

# Instantiate Singleton
technical_agent_service = TechnicalAgentService()
