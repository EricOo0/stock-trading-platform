import logging
import asyncio
import uuid
from typing import Dict, Any
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from backend.infrastructure.config.loader import config
from .tools import search_web, inspect_page, fetch_reddit_rss
from .prompts import WORKER_INSTRUCTION
from .schemas import NewsTask

logger = logging.getLogger(__name__)

class WorkerAgent:
    def __init__(self, event_queue: asyncio.Queue):
        self.event_queue = event_queue
        self._configure_llm()
        self.model_name = config.get("model", "deepseek-ai/DeepSeek-V3.1-Terminus")
        if not self.model_name.startswith("openai/"):
            self.model_name = f"openai/{self.model_name}"

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

    def _create_inner_agent(self, callbacks: Dict[str, Any]) -> Agent:
        return Agent(
            name="news_sentiment_worker",
            model=self.model_name,
            instruction=WORKER_INSTRUCTION,
            tools=[search_web, inspect_page, fetch_reddit_rss],
            description="Worker agent for deep research.",
            **callbacks
        )

    async def execute(self, task: NewsTask, global_context: str = "") -> str:
        """
        Executes a specific task.
        """
        from .callbacks import TaskCallbackHandler
        
        handler = TaskCallbackHandler(self.event_queue, task_id=task.id)
        callbacks = {
            "before_tool_callback": handler.on_tool_start,
            "after_tool_callback": handler.on_tool_end,
            "before_model_callback": handler.on_model_start,
            "after_model_callback": handler.on_model_end,
        }
        
        agent = self._create_inner_agent(callbacks)
        
        prompt = f"""
        【当前任务】
        标题: {task.title}
        描述: {task.description}
        
        【全局背景】
        {global_context}
        
        请开始执行任务。
        务必遵守 INSTRUCTION 的要求：
        1. 深度挖掘，多轮搜索。
        2. 最终输出必须包含【待跟进问题】章节，格式为 `## 待跟进问题`。
        """
        
        logger.info(f"[Worker] Starting execution for Task: {task.id} (Name: {task.title}, Description: {task.description[:50]}...)")
        
        try:
            session_service = InMemorySessionService()
            session_id = str(uuid.uuid4())
            await session_service.create_session(
                session_id=session_id,
                user_id="worker_user",
                app_name="news_sentiment_worker_app"
            )
            runner = Runner(agent=agent, session_service=session_service, app_name="news_sentiment_worker_app")
            
            msg = types.Content(role="user", parts=[types.Part(text=prompt)])
            
            # Run agent loop
            async for _ in runner.run_async(session_id=session_id, user_id="worker_user", new_message=msg):
                pass
            
            # Retrieve final response from handler
            # history = await session_service.get_session_history(session_id)
            # response_text = ""
            # if history and history[-1].role == 'model':
            #    parts = history[-1].parts
            #    response_text = "".join([p.text for p in parts if p.text])
            
            response_text = handler.last_response_text
            
            return response_text if response_text else "任务执行完成（无文本输出）"
            
        except Exception as e:
            logger.error(f"[Worker] Execution failed: {e}", exc_info=True)
            return f"执行出错: {str(e)}"
