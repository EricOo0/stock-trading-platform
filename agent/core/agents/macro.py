import functools
from core.prompts import MACRO_AGENT_SYSTEM_PROMPT
from .utils import create_agent, agent_node

def create_macro_node(llm, tools):
    agent = create_agent(llm, tools, MACRO_AGENT_SYSTEM_PROMPT)
    return functools.partial(agent_node, agent=agent, name="MacroDataInvestigator")

# --- A2A Integration ---
from fastapi import APIRouter, FastAPI, Request
from core.config import Config
from .a2a_base import BaseA2AAgent
from skills.macro_data_tool.skill import MacroDataSkill

class MacroA2A(BaseA2AAgent):
    def __init__(self, config: Config, event_bus=None):
        super().__init__(
            config, 
            "MacroDataInvestigator", 
            "Analyzes macroeconomic data like GDP, CPI, etc.",
            ["macro_analysis"],
            [MacroDataSkill()],
            MACRO_AGENT_SYSTEM_PROMPT,
            event_bus=event_bus
        )

def setup_a2a(app: FastAPI, config: Config):
    """Setup Macro A2A agent."""
    agent = MacroA2A(config)
    router = APIRouter(prefix="/a2a", tags=["A2A"])
    
    @router.get("/macrodatainvestigator/.well-known/agent.json", tags=[agent.card.name])
    async def get_card():
        return agent.card.dict()
        
    @router.post("/macrodatainvestigator/run", tags=[agent.card.name])
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
            agent = MacroA2A(config)
            logger.info("Macro Agent initialized.")
            
            # 3. Create Test Task
            test_message = "What is the current US GDP growth rate?"
            
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
