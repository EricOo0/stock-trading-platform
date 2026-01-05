import logging
import asyncio
import uuid
import json
from typing import Dict, Any, Optional, AsyncGenerator

from backend.infrastructure.browser.steel_browser import browser_engine

logger = logging.getLogger(__name__)

class NewsSentimentService:
    def __init__(self):
        # We don't strictly need session service if we are bypassing Runner for now
        # But keeping it if we want to store history later
        pass

    async def start_research(self, session_id: str, query: str) -> AsyncGenerator[str, None]:
        """
        Streaming version of start_research using Master-Worker Orchestrator.
        Yields NDJSON events.
        """
        try:
            # 1. Attach Browser Engine
            if session_id:
                try:
                    await browser_engine.initialize_session(session_id=session_id)
                except Exception:
                    pass
            
            # 2. Setup Queue
            event_queue = asyncio.Queue()
            
            # 3. Define Orchestrator Runner
            async def run_orchestrator():
                try:
                    from backend.app.agents.news_sentiment.agent import create_news_sentiment_agent
                    
                    # Create the custom Orchestrator
                    orchestrator = create_news_sentiment_agent(event_queue=event_queue)
                    
                    # Execute
                    await orchestrator.run(user_query=query)
                    
                except Exception as e:
                    logger.error(f"Orchestrator Execution Error: {e}", exc_info=True)
                    error_event = {"type": "error", "content": f"Internal Error: {str(e)}"}
                    await event_queue.put(json.dumps(error_event) + "\n")
                finally:
                    # Send stop signal
                    await event_queue.put(None)

            # 4. Start Background Task
            asyncio.create_task(run_orchestrator())

            # 5. Consume Queue & Yield
            while True:
                item = await event_queue.get()
                if item is None:
                    break
                yield item

        except Exception as e:
            logger.error(f"News Sentiment Service Error: {e}", exc_info=True)
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

news_sentiment_service = NewsSentimentService()
