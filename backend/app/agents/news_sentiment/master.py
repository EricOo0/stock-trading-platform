import logging
import json
import asyncio
import time
import uuid
from typing import List, Dict, Any, Literal
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from backend.infrastructure.config.loader import config
from .prompts import MASTER_INSTRUCTION
from .schemas import NewsPlan, NewsTask, TaskStatus, AgentType, EventType, SentimentResult

logger = logging.getLogger(__name__)

class MasterAgent:
    def __init__(self, event_queue: asyncio.Queue, plan: NewsPlan):
        self.event_queue = event_queue
        self.plan = plan
        self._configure_llm()
        self.model_name = config.get("model", "deepseek-ai/DeepSeek-V3.1-Terminus")
        if not self.model_name.startswith("openai/"):
            self.model_name = f"openai/{self.model_name}"
        
        self.conclusion: SentimentResult = None

    def _configure_llm(self):
        import os
        if "OPENAI_API_BASE" not in os.environ:
             os.environ["OPENAI_API_BASE"] = config.get("api_url", "https://api.siliconflow.cn/v1")
        
        current_key = os.environ.get("OPENAI_API_KEY", "")
        if not current_key or current_key.startswith("sk-xxxx"):
             api_keys = config.get("api_keys", {})
             sf_key = api_keys.get("siliconflow")
             openai_key = api_keys.get("openai")
             
             if sf_key and not sf_key.startswith("sk-xxxx"):
                 os.environ["OPENAI_API_KEY"] = sf_key
             elif openai_key and not openai_key.startswith("sk-xxxx"):
                 os.environ["OPENAI_API_KEY"] = openai_key

    def _get_tools(self):
        def create_plan(tasks: List[Dict[str, str]]) -> str:
            try:
                new_tasks = []
                for idx, t in enumerate(tasks):
                    task_id = f"task_{int(time.time())}_{idx}"
                    new_task = NewsTask(
                        id=task_id,
                        title=t.get('title', 'Untitled'),
                        description=t.get('description', ''),
                        status=TaskStatus.PENDING,
                        agent_type=AgentType.WORKER 
                    )
                    new_tasks.append(new_task)
                self.plan.tasks.extend(new_tasks)
                self._emit_plan_update()
                return f"Plan created with {len(new_tasks)} tasks."
            except Exception as e:
                logger.error(f"create_plan failed: {e}")
                return f"Error creating plan: {e}"

        def add_tasks(tasks: List[Dict[str, str]]) -> str:
            try:
                new_tasks = []
                for idx, t in enumerate(tasks):
                    task_id = f"task_{int(time.time())}_{idx}"
                    new_task = NewsTask(
                        id=task_id,
                        title=t.get('title', 'Untitled'),
                        description=t.get('description', ''),
                        status=TaskStatus.PENDING,
                        agent_type=AgentType.WORKER
                    )
                    new_tasks.append(new_task)
                self.plan.tasks.extend(new_tasks)
                self._emit_plan_update()
                return f"Added {len(new_tasks)} new tasks."
            except Exception as e:
                return f"Error adding tasks: {e}"

        def generate_conclusion(ticker: str, sentiment: str, trend: str, title: str, summary: str) -> str:
            try:
                if trend not in ["up", "down", "neutral"]:
                    trend = "neutral"
                result = SentimentResult(
                    ticker=ticker,
                    sentiment=sentiment,
                    trend=trend, # type: ignore
                    title=title,
                    summary=summary
                )
                self.conclusion = result
                event = {
                    "type": EventType.CONCLUSION,
                    "payload": result.model_dump()
                }
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self.event_queue.put(json.dumps(event) + "\n"))
                except RuntimeError:
                    pass
                return "Conclusion generated successfully. Research complete."
            except Exception as e:
                return f"Error generating conclusion: {e}"

        return [create_plan, add_tasks, generate_conclusion]

    def _emit_plan_update(self):
        try:
            event = {
                "type": EventType.PLAN_UPDATE,
                "payload": self.plan.model_dump()
            }
            loop = asyncio.get_running_loop()
            loop.create_task(self.event_queue.put(json.dumps(event) + "\n"))
        except Exception:
            pass

    async def run_step(self, context: str) -> str:
        master_task_id = "master_planning"
        from .callbacks import TaskCallbackHandler
        handler = TaskCallbackHandler(self.event_queue, task_id=master_task_id)
        
        callbacks = {
            "before_tool_callback": handler.on_tool_start,
            "after_tool_callback": handler.on_tool_end,
            "before_model_callback": handler.on_model_start,
            "after_model_callback": handler.on_model_end,
        }
        
        tools = self._get_tools()
        
        agent = Agent(
            name="news_sentiment_master",
            model=self.model_name,
            instruction=MASTER_INSTRUCTION,
            tools=tools,
            description="Master Analyst",
            **callbacks
        )
        
        plan_status = "Current Plan Status:\n"
        if not self.plan.tasks:
            plan_status += "No tasks yet. Please create a plan."
        else:
            for t in self.plan.tasks:
                plan_status += f"- [{t.status.value}] {t.title}: {t.result if t.result else '(No result yet)'}\n"
        
        prompt = f"""
        {context}
        
        {plan_status}
        
        Please review the status and decide the next step (Create Plan, Add Tasks, or Conclude).
        """
        
        logger.info("[Master] Running step...")
        
        session_service = InMemorySessionService()
        session_id = str(uuid.uuid4())
        await session_service.create_session(
            session_id=session_id,
            user_id="master_user",
            app_name="news_sentiment_master_app"
        )
        runner = Runner(agent=agent, session_service=session_service, app_name="news_sentiment_master_app")
        
        msg = types.Content(role="user", parts=[types.Part(text=prompt)])
        
        async for _ in runner.run_async(session_id=session_id, user_id="master_user", new_message=msg):
            pass
            
        # history = await session_service.get_session_history(session_id)
        # response_text = ""
        # if history and history[-1].role == 'model':
        #      parts = history[-1].parts
        #      response_text = "".join([p.text for p in parts if p.text])
        
        # Use handler's captured response
        response_text = handler.last_response_text
        
        return response_text
