from loguru import logger
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from core.state import AgentState
from core.prompts import RECEPTIONIST_SYSTEM_PROMPT
from core.a2a_client import call_a2a_agent_direct, A2ATaskResponse


async def receptionist_node(state: AgentState, llm: ChatOpenAI):
    """Analyzes user intent and creates a Research Brief."""
    try:
        logger.info("DEBUG: Receptionist analyzing intent...")
        messages = state["messages"]

        # Analyze user intent locally
        chain = (
            ChatPromptTemplate.from_messages(
                [
                    ("system", RECEPTIONIST_SYSTEM_PROMPT),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )
            | llm
        )
        result = chain.invoke(state)
        brief = result.content
        logger.info(f"DEBUG: Research Brief: {brief}")

        # Set name for frontend
        result.name = "Receptionist"

        # Initialize evidence log if not present
        evidence_log = state.get("evidence_log", [])

        return {
            "messages": [result],
            "research_brief": brief,
            "evidence_log": evidence_log,
            "review_count": 0,
        }
    except Exception as e:
        logger.error(f"Receptionist error: {e}")
        import traceback

        traceback.print_exc()
        # Fallback: Pass original query as brief
        return {
            "messages": [
                AIMessage(
                    content="System Error in Receptionist. Proceeding with raw query.",
                    name="Receptionist",
                )
            ],
            "research_brief": (
                state["messages"][-1].content if state["messages"] else "Analyze market"
            ),
            "evidence_log": [],
            "review_count": 0,
        }


def get_receptionist_card():
    """Returns the A2A Agent Card for the Receptionist."""
    return {
        "name": "Receptionist",
        "description": "The entry point for the Stock Analysis System. Analyzes user intent and creates a research brief.",
        "capabilities": ["intent_analysis", "research_planning"],
        "input_schema": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
        "output_schema": {
            "type": "object",
            "properties": {"response": {"type": "string"}},
        },
        "version": "1.0.0",
    }


# --- A2A Integration ---
from fastapi import APIRouter, FastAPI, Request
from a2a.types import AgentCard, Task
from langchain_core.messages import HumanMessage
from core.config import Config


class ReceptionistA2A:
    def __init__(self, config: Config, event_bus=None):
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=0.1,
            openai_api_key=config.llm.api_key,
            openai_api_base=config.llm.api_base,
        )
        self.event_bus = event_bus
        card_data = get_receptionist_card()
        self.card = AgentCard(
            name=card_data["name"],
            description=card_data["description"],
            version=card_data["version"],
            capabilities={"skills": card_data["capabilities"]},
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[],
            url="http://localhost:8001/a2a/receptionist",
            topics=["stock", "finance"],
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

            # Publish start event
            await self.publish_event("agent_start", "Analyzing user intent...", task.context_id, status="thinking")

            state = {
                "messages": [HumanMessage(content=message)],
                "research_brief": "",
                "evidence_log": [],
                "review_count": 0,
                "next": "",
                "plan": [],
            }
            
            # Run node (we might want to make this async-aware or use ainvoke if possible, 
            # but receptionist_node is async defined in this file)
            result = await receptionist_node(state, self.llm)
            
            brief = result.get("research_brief")
            
            # Publish completion event
            await self.publish_event("agent_message", brief, task.context_id, status="speaking")
            await self.publish_event("agent_end", "Intent analysis complete", task.context_id, status="completed")
            
            return {"response": brief, "steps": []}
        except Exception as e:
            logger.error(f"A2A Receptionist Error: {e}")
            if task and task.context_id:
                await self.publish_event("error", str(e), task.context_id)
            return {"error": str(e)}


def setup_a2a(app: FastAPI, config: Config):
    """Setup Receptionist A2A agent."""
    agent = ReceptionistA2A(config)
    router = APIRouter(prefix="/a2a", tags=["A2A"])

    @router.get("/receptionist/.well-known/agent.json", tags=[agent.card.name])
    async def get_card():
        return agent.card.dict()

    @router.post("/receptionist/run", tags=[agent.card.name])
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
            agent = ReceptionistA2A(config)
            logger.info("Receptionist initialized.")

            # 3. Create Test Task
            test_message = (
                "Analyze the stock price of Apple (AAPL) and its recent news sentiment."
            )

            task = Task(
                id=str(uuid.uuid4()),
                contextId=str(uuid.uuid4()),
                status=TaskStatus(state="submitted"),
                history=[
                    Message(
                        messageId=str(uuid.uuid4()),
                        role=Role.user,
                        parts=[TextPart(text=test_message)],
                    )
                ],
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
