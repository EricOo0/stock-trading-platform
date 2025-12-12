import json
import logging
import traceback
from typing import AsyncGenerator, Optional
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import the Chairman Agent
from backend.app.agents.fintech.chairman import chairman_agent

logger = logging.getLogger(__name__)

class FintechService:
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.app_name = "fintech_chairman"
        
    async def chat_stream(self, query: str, user_id: str, session_id: str) -> AsyncGenerator[str, None]:
        """
        Streams events from the Fintech Agent.
        """
        try:
            # Create session if needed
            try:
                await self.session_service.create_session(
                    app_name=self.app_name, 
                    user_id=user_id, 
                    session_id=session_id
                )
            except Exception as e:
                # Ignore if session already exists
                pass

            runner = Runner(
                agent=chairman_agent, 
                app_name=self.app_name, 
                session_service=self.session_service
            )
            
            content = types.Content(role='user', parts=[types.Part(text=query)])
            
            # Start running
            events = runner.run_async(user_id=user_id, session_id=session_id, new_message=content)
            
            async for event in events:
                try:
                    # 1. Handle Thoughts / Text Content
                    if hasattr(event, 'content') and event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                message = {
                                    "type": "chunk", 
                                    "content": part.text
                                }
                                yield json.dumps(message, ensure_ascii=False) + "\n"
                    
                    # 2. Handle Tool Calls
                    if hasattr(event, 'tool_calls') and event.tool_calls:
                         for tool_call in event.tool_calls:
                             # Safe access to function name and arguments
                             fn_name = getattr(tool_call.function, 'name', 'tool')
                             fn_args = getattr(tool_call.function, 'arguments', '{}')
                             
                             message = {
                                 "type": "thought",
                                 "content": f"Use {fn_name}({fn_args})"
                             }
                             yield json.dumps(message, ensure_ascii=False) + "\n"

                    # 3. Handle Tool Outputs
                    if hasattr(event, 'tool_outputs') and event.tool_outputs:
                        for tool_output in event.tool_outputs:
                             raw = str(getattr(tool_output, 'tool_response', ''))
                             truncated_output = raw[:200] + "..." if len(raw) > 200 else raw
                             message = {
                                 "type": "thought",
                                 "content": f"Observation: {truncated_output}"
                             }
                             yield json.dumps(message, ensure_ascii=False) + "\n"

                except Exception as e:
                    logger.error(f"Error processing event: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Fintech Service Error: {e}")
            traceback.print_exc()
            yield json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False) + "\n"

    async def chat_oneshot(self, query: str, user_id: str, session_id: str) -> str:
        """
        Executes the agent and returns the full accumulated response text.
        Useful for internal service-to-service calls where streaming is not needed.
        """
        logger.info(f"Executing oneshot chat for session {session_id}")
        full_response = ""
        
        async for chunk in self.chat_stream(query, user_id, session_id):
            try:
                data = json.loads(chunk)
                # We only care about the final text content chunks for the result
                if data.get("type") == "chunk":
                     full_response += data.get("content", "")
            except Exception as e:
                logger.warning(f"Error parsing chunk in oneshot: {e}")
                
        return full_response

fintech_service = FintechService()
