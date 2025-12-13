import logging
import asyncio
import uuid
from typing import Dict, Any, Optional, AsyncGenerator

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from backend.infrastructure.browser.steel_browser import browser_engine

logger = logging.getLogger(__name__)

class DeepSearchService:
    def __init__(self):
        # Initialize with InMemorySessionService
        self.session_service = InMemorySessionService()

    async def start_research(self, session_id: str, query: str) -> AsyncGenerator[str, None]:
        """
        Streaming version of start_research.
        Yields NDJSON events: {'type': 'thought'|'tool'|'result', 'content': ...}
        """
        import json
        try:
            # 1. Attach Browser Engine
            if session_id:
                try:
                    await browser_engine.initialize_session(session_id=session_id)
                except Exception:
                    pass
            
            # 2. Prepare Input
            adk_session_id = session_id or str(uuid.uuid4())
            user_id = "deep_search_user"
            input_content = types.Content(role="user", parts=[types.Part(text=query)])
            
            # 3. Create Session
            try:
                await self.session_service.create_session(
                    app_name="deep_search_app",
                    user_id=user_id,
                    session_id=adk_session_id
                )
            except:
                pass


            # 4. Stream Agent Execution using Queue + Callback
            from backend.app.agents.deep_search.agent import create_deep_search_agent
            from google.adk.runners import Runner

            # Queue for events
            event_queue = asyncio.Queue()
            
            # Helper to run the agent and signal finish
            async def run_agent():
                try:
                    # Create Agent with Callbacks linked to queue
                    local_agent = create_deep_search_agent(event_queue=event_queue)
                    
                    # Create Runner
                    local_runner = Runner(
                        agent=local_agent,
                        app_name="deep_search_app",
                        session_service=self.session_service
                    )
                    
                    # Run it
                    exec_events = local_runner.run_async(
                        user_id=user_id,
                        session_id=adk_session_id,
                        new_message=input_content
                    )
                    
                    async for event in exec_events:
                        # 其实这个可以在 on_mode_end的callback里实现
                        # Only capture Text Chunks via the stream (thoughts)
                        # Tools are handled by the callback side-channel
                        if hasattr(event, 'content') and event.content and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    # Emit 'thought' event for streaming text
                                    msg = {"type": "thought", "content": part.text}
                                    await event_queue.put(json.dumps(msg) + "\n")

                except Exception as e:
                    logger.error(f"Agent Execution Error: {e}")
                    await event_queue.put(json.dumps({"type": "error", "content": str(e)}) + "\n")
                finally:
                    # Send special stop signal
                    await event_queue.put(None)

            # Start background task
            asyncio.create_task(run_agent())

            # Consume Queue
            while True:
                item = await event_queue.get()
                if item is None:
                    break
                yield item

        except Exception as e:
            logger.error(f"Deep Search Service Error: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"
            
        except Exception as e:
            logger.error(f"Deep Search Service Error: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

deep_search_service = DeepSearchService()
