from typing import Any, Dict, List
from a2a.types import AgentCard, Task
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from core.config import Config
from core.agents.utils import create_agent, run_react_agent

class BaseA2AAgent:
    def __init__(self, config: Config, name: str, description: str, capabilities: List[str], tools: List[Any], system_prompt: str, event_bus=None):
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=0.1, 
            openai_api_key=config.llm.api_key,
            openai_api_base=config.llm.api_base,
        )
        self.tools = tools
        self.internal_agent = create_agent(self.llm, tools, system_prompt)
        self.event_bus = event_bus
        
        self.card = AgentCard(
            name=name,
            description=description,
            version="1.0.0",
            capabilities={"skills": capabilities}, # capabilities is AgentCapabilities (dict)
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[], # Required list of AgentSkill
            url=f"http://localhost:8001/a2a/{name.lower()}", # Placeholder URL
            topics=["stock", "finance"]
        )

    async def publish_event(self, type: str, content: str = None, session_id: str = None, **kwargs):
        """Publish an event to the bus."""
        if self.event_bus and session_id:
            from core.bus import Event
            event = Event(
                type=type,
                session_id=session_id,
                agent=self.card.name,
                content=content,
                metadata=kwargs
            )
            await self.event_bus.publish(event)

    async def run_task(self, task: Task) -> Dict[str, Any]:
        try:
            # Extract message from history
            message = ""
            if task.history:
                last_msg = task.history[-1]
                for part in last_msg.parts:
                    if part.root.kind == "text":
                        message += part.root.text
            
            if not message:
                return {"error": "No message provided in task history"}
            
            logger.info(f"A2A {self.card.name}: Received task: {message}")
            
            # Set agent name for logging
            self.internal_agent.name = self.card.name
            
            # Publish start event
            await self.publish_event("agent_start", f"{self.card.name} started working", task.context_id, status="thinking")

            result = await run_react_agent(
                self.internal_agent, 
                self.tools, 
                [HumanMessage(content=message)],
                event_bus=self.event_bus,
                session_id=task.context_id,
                agent_name=self.card.name
            )
            
            # Publish end event
            await self.publish_event("agent_end", f"{self.card.name} completed task", task.context_id, status="completed")
            
            return result # Contains response and steps
                
        except Exception as e:
            logger.error(f"A2A {self.card.name} Error: {e}")
            if task and task.context_id:
                await self.publish_event("error", str(e), task.context_id)
            return {"error": str(e)}
