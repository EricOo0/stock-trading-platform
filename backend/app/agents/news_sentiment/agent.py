import asyncio
import logging
from typing import Optional, List

from backend.infrastructure.config.loader import config
from .schemas import NewsPlan, TaskStatus, AgentType, EventType
from .master import MasterAgent
from .worker import WorkerAgent

logger = logging.getLogger(__name__)

class NewsSentimentAgent:
    """
    Orchestrator for the Master-Worker News Sentiment Agent.
    """
    def __init__(self, event_queue: asyncio.Queue):
        self.event_queue = event_queue
        self.plan = NewsPlan()
        self.master = MasterAgent(event_queue, self.plan)
        self.worker = WorkerAgent(event_queue)

    async def run(self, user_query: str):
        """
        Main execution loop.
        """
        logger.info(f"[Orchestrator] Starting run for query: {user_query}")
        
        try:
            # Phase 1: Initial Planning
            context = f"User Goal: {user_query}\nTimestamp: {self._get_timestamp()}"
            logger.info("[Orchestrator] Invoking Master for Initial Planning...")
            await self.master.run_step(context)
            logger.info("[Orchestrator] Master Initial Planning Complete.")
            
            # Phase 2 & 3: Execution Loop
            max_turns = 15
            for turn in range(max_turns):
                logger.info(f"[Orchestrator] Turn {turn+1}/{max_turns}")
                
                # Check for Conclusion first
                if self.master.conclusion:
                    logger.info("[Orchestrator] Conclusion reached via Master.")
                    break
                
                # Identify Pending Tasks
                pending_tasks = [t for t in self.plan.tasks if t.status == TaskStatus.PENDING]
                
                if not pending_tasks:
                    logger.info("[Orchestrator] No pending tasks. Consulting Master for next step...")
                    # No pending tasks, ask Master for direction (Reflect/Conclude)
                    # If previously we had tasks and now none, Master needs to see results
                    await self.master.run_step("No pending tasks. Review results and decide: Add Tasks or Conclude?")
                    if self.master.conclusion:
                        break
                    # If Master didn't add tasks and didn't conclude, force it?
                    # We check if tasks were added
                    new_pending = [t for t in self.plan.tasks if t.status == TaskStatus.PENDING]
                    if not new_pending:
                        logger.warning("[Orchestrator] Master did not add tasks or conclude. Forcing conclusion request.")
                        await self.master.run_step("You must either add tasks to investigate further OR generate a conclusion now.")
                        if not self.master.conclusion:
                             # Fallback conclusion if stuck
                             break 
                else:
                    logger.info(f"[Orchestrator] Found {len(pending_tasks)} pending tasks. Starting concurrent execution...")
                    
                    # Limit concurrency to avoid rate limits
                    semaphore = asyncio.Semaphore(3)
                    
                    async def _execute_task_safe(task, ctx, sem):
                        async with sem:
                            try:
                                logger.info(f"[Orchestrator] Starting Task {task.id}")
                                task.status = TaskStatus.IN_PROGRESS
                                self.master._emit_plan_update()
                                
                                result = await self.worker.execute(task, ctx)
                                logger.info(f"[Orchestrator] Task {task.id} completed. Result len={len(result)}")
                                
                                task.result = result
                                task.status = TaskStatus.COMPLETED
                            except Exception as e:
                                logger.error(f"[Orchestrator] Task {task.id} failed: {e}")
                                task.status = TaskStatus.FAILED
                                task.result = f"Execution Error: {str(e)}"
                            finally:
                                self.master._emit_plan_update()

                    # Create coroutines
                    tasks_coroutines = [
                        _execute_task_safe(task, context, semaphore) 
                        for task in pending_tasks
                    ]
                    
                    # Execute all concurrently
                    await asyncio.gather(*tasks_coroutines)
                    logger.info("[Orchestrator] Batch execution completed.")
            
            # Final check
            if not self.master.conclusion:
                 await self.master.run_step("Final call: Please generate a conclusion based on available information.")

        except Exception as e:
            logger.error(f"[Orchestrator] Run failed: {e}", exc_info=True)
            # Emit error event
            # ...

    def _get_timestamp(self):
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Factory function to maintain some compatibility in signature, 
# though return type is different.
def create_news_sentiment_agent(event_queue: asyncio.Queue) -> NewsSentimentAgent:
    return NewsSentimentAgent(event_queue)
