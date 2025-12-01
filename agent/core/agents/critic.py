from loguru import logger
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from core.state import AgentState
from core.prompts import CRITIC_SYSTEM_PROMPT

def critic_node(state: AgentState, llm: ChatOpenAI):
    """Reviews evidence and synthesizes final answer."""
    try:
        logger.info("DEBUG: Critic reviewing evidence...")
        
        # Extract only relevant messages (Research Brief + Evidence)
        messages = state["messages"]
        relevant_messages = []
        
        # Find the Research Brief (from Receptionist)
        for msg in messages:
            if hasattr(msg, 'name') and msg.name == "Receptionist":
                relevant_messages.append(msg)
                break
        
        # Collect all evidence from specialists
        specialist_names = ["MarketDataInvestigator", "MacroDataInvestigator", 
                           "SentimentInvestigator", "WebSearchInvestigator"]
        for msg in messages:
            if hasattr(msg, 'name') and msg.name in specialist_names:
                # Only include messages with "EVIDENCE" keyword
                if "EVIDENCE" in msg.content.upper():
                    relevant_messages.append(msg)
        
        logger.info(f"DEBUG: Critic processing {len(relevant_messages)} relevant messages")
        
        # Create chain with filtered messages
        chain = (
            ChatPromptTemplate.from_messages([
                ("system", CRITIC_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="messages"),
            ])
            | llm
        )
        
        result = chain.invoke({"messages": relevant_messages})
        logger.info("DEBUG: Critic synthesis complete.")
        
        # Set name for frontend
        result.name = "Critic"
        
        return {"messages": [result]}
    except Exception as e:
        logger.error(f"Critic error: {e}")
        return {"messages": [AIMessage(content="System Error in Critic. Please check logs.", name="Critic")]}

# --- A2A Integration ---
from fastapi import APIRouter, FastAPI, Request
from a2a.types import AgentCard, Task
from core.config import Config

class CriticA2A:
    def __init__(self, config: Config, event_bus=None):
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=0.1, 
            openai_api_key=config.llm.api_key,
            openai_api_base=config.llm.api_base,
        )
        self.event_bus = event_bus
        self.card = AgentCard(
            name="Critic",
            description="Reviews evidence and synthesizes the final answer.",
            version="1.0.0",
            capabilities={"skills": ["synthesis", "review"]},
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[],
            url="http://localhost:8001/a2a/critic",
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

    async def run_task(self, task: Task) -> dict:
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
            
            logger.info(f"Critic A2A: Received task: {message}")
            
            # Publish start event
            await self.publish_event("agent_start", "Reviewing evidence and synthesizing final answer...", task.context_id, status="thinking")
            
            # Critic expects messages with specific names or content
            # For A2A test, we simulate a simple state
            state = {
                "messages": [
                    HumanMessage(content="Research Brief: " + message, name="Receptionist"),
                    HumanMessage(content="EVIDENCE: Some simulated evidence.", name="MarketDataInvestigator")
                ]
            }
            
            # Publish status change
            await self.publish_event("agent_status_change", "Analyzing evidence...", task.context_id, status="thinking")
            
            result = critic_node(state, self.llm)
            response_msg = result["messages"][-1]
            
            # Publish message event
            await self.publish_event("agent_message", response_msg.content, task.context_id, status="speaking")
            
            # Publish end event
            await self.publish_event("agent_end", "Synthesis complete", task.context_id, status="completed")
            
            return {
                "response": response_msg.content,
                "steps": []
            }
        except Exception as e:
            logger.error(f"A2A Critic Error: {e}")
            # Publish error event
            if hasattr(task, 'context_id'):
                await self.publish_event("error", str(e), task.context_id)
            return {"error": str(e)}

def setup_a2a(app: FastAPI, config: Config):
    """Setup Critic A2A agent."""
    agent = CriticA2A(config)
    router = APIRouter(prefix="/a2a", tags=["A2A"])
    
    @router.get("/critic/.well-known/agent.json", tags=[agent.card.name])
    async def get_card():
        return agent.card.dict()
        
    @router.post("/critic/run", tags=[agent.card.name])
    async def run_agent(request: Request):
        data = await request.json()
        class SimpleTask:
            def __init__(self, input_data):
                self.input = input_data
        return await agent.run_task(SimpleTask(data))
        
    app.include_router(router)

if __name__ == "__main__":
    import asyncio
    from core.config import get_config
    from a2a.types import TaskStatus, Message, Role, TextPart
    import uuid
    
    async def main():
        try:
            # 1. Load Config
            config = get_config()
            logger.info("Config loaded.")
            
            # 2. Initialize Agent
            agent = CriticA2A(config)
            logger.info("Critic initialized.")
            
            # 3. Create Test Task
            test_message = "Apple stock is rising due to strong earnings."
            
            task = Task(
                id=str(uuid.uuid4()),
                contextId=str(uuid.uuid4()),
                status=TaskStatus(state="submitted"),
                history=[
                    Message(
                        messageId=str(uuid.uuid4()),
                        role=Role.user,
                        parts=[TextPart(text=test_message)]
                    )
                ]
            )
            
            # 4. Run Task
            logger.info(f"Running task: {test_message}")
            result = await agent.run_task(task)
            
            # 5. Print Result
            import json
            print("\n--- Result ---")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(main())
