from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import uuid

from core.state import AgentState
from core.prompts import CHAIRMAN_SYSTEM_PROMPT
from core.schema import CallAgent


def create_chairman_chain(chairman_llm: ChatOpenAI):
    """Create the chairman chain with CallAgent tool binding."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CHAIRMAN_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    return prompt | chairman_llm.bind_tools([CallAgent], tool_choice="auto")


async def chairman_node(state: AgentState, chairman_llm: ChatOpenAI):
    """Chairman orchestrates specialists using dynamic ReAct loop."""
    try:
        # Import A2A agents here to avoid circular dependencies
        from core.agents.macro import MacroA2A
        from core.agents.market import MarketA2A
        from core.agents.sentiment import SentimentA2A
        from core.agents.web_search import WebSearchA2A
        from core.config import Config, get_config
        from a2a.types import (
            Task as A2ATask,
            TaskStatus,
            Message as A2AMessage,
            Role,
            TextPart,
        )
        import uuid

        messages = state.get("messages", [])
        review_count = state.get("review_count", 0)

        # Recursion limit
        if review_count > 10:
            logger.warning("Chairman: Recursion limit reached. Forcing FINISH.")
            return {"next": "FINISH", "review_count": review_count}

        # Get config for A2A agents
        config = get_config()

        # Initialize A2A specialist agents
        agent_map = {
            "MacroDataInvestigator": MacroA2A(config),
            "MarketDataInvestigator": MarketA2A(config),
            "SentimentInvestigator": SentimentA2A(config),
            "WebSearchInvestigator": WebSearchA2A(config),
        }

        # Check if this is a streaming context
        if state.get("streaming", False):
            # Return state for streaming processing
            return {
                "messages": messages,
                "review_count": review_count,
                "agent_map": agent_map,
                "config": config,
                "streaming": True,
            }

        # ReAct Loop
        max_iterations = 5
        iteration = 0

        logger.info("Chairman: Starting ReAct loop...")

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Chairman: Iteration {iteration}/{max_iterations}")

            # Invoke Chairman LLM
            chairman_chain = create_chairman_chain(chairman_llm)
            result = chairman_chain.invoke({"messages": messages})
            result.name = "Chairman"

            # Check for tool calls
            if not result.tool_calls:
                logger.info(
                    "Chairman: No tool call - task complete. Routing to Critic for final synthesis."
                )

                # Call Critic for final synthesis
                from core.agents.critic import CriticA2A

                critic_agent = CriticA2A(config)

                # Create task for Critic with all conversation history
                critic_instruction = "Review all evidence gathered and provide a comprehensive final analysis."
                critic_task = A2ATask(
                    id=str(uuid.uuid4()),
                    context_id=str(uuid.uuid4()),
                    status=TaskStatus(state="submitted"),
                    history=[
                        A2AMessage(
                            messageId=str(uuid.uuid4()),
                            role=Role.user,
                            parts=[TextPart(text=critic_instruction)],
                        )
                    ],
                )

                logger.info("Chairman: Calling Critic for final synthesis...")
                critic_result = await critic_agent.run_task(critic_task)
                critic_response = critic_result.get(
                    "response", "Critic synthesis unavailable"
                )

                logger.info(f"Chairman: Critic synthesis complete")

                # Chairman decided task is complete
                return {
                    "messages": [result],
                    "next": "FINISH",
                    "critic_synthesis": critic_response,
                    "review_count": review_count + 1,
                }

            # Execute tool call
            tool_call = result.tool_calls[0]
            if tool_call["name"] != "CallAgent":
                logger.warning(f"Chairman: Unexpected tool call: {tool_call['name']}")
                continue

            args = tool_call["args"]
            agent_name = args.get("agent")
            instruction = args.get("instruction")

            logger.info(
                f"Chairman: Calling {agent_name} with instruction: {instruction}"
            )

            # Get specialist A2A agent
            specialist_agent = agent_map.get(agent_name)
            if not specialist_agent:
                logger.error(f"Chairman: Unknown agent: {agent_name}")
                continue

            # Create A2A Task for specialist
            a2a_task = A2ATask(
                id=str(uuid.uuid4()),
                context_id=str(uuid.uuid4()),
                status=TaskStatus(state="submitted"),
                history=[
                    A2AMessage(
                        messageId=str(uuid.uuid4()),
                        role=Role.user,
                        parts=[TextPart(text=instruction)],
                    )
                ],
            )

            # Execute specialist via A2A
            specialist_result = await specialist_agent.run_task(a2a_task)

            # Extract specialist's response
            specialist_response = specialist_result.get("response", "No response")
            specialist_steps = specialist_result.get("steps", [])

            logger.info(
                f"Chairman: {agent_name} responded with {len(specialist_steps)} steps"
            )

            # Format response with evidence
            evidence_summary = f"EVIDENCE from {agent_name}:\n{specialist_response}"
            if specialist_steps:
                evidence_summary += f"\n\nTool calls made: {len(specialist_steps)}"

            # Add to conversation history
            messages.append(result)  # Chairman's decision
            messages.append(
                ToolMessage(content=evidence_summary, tool_call_id=tool_call["id"])
            )

        # Max iterations reached
        logger.warning("Chairman: Max iterations reached")
        return {
            "messages": messages,
            "next": "Critic",
            "review_count": review_count + 1,
        }

    except Exception as e:
        logger.error(f"Chairman error: {e}")
        import traceback

        traceback.print_exc()
        return {"next": "FINISH", "review_count": state.get("review_count", 0) + 1}


# --- A2A Integration ---
# --- A2A Integration ---
from fastapi import APIRouter, FastAPI, Request
from a2a.types import AgentCard, Task, TaskStatus, Message, Role, TextPart
from core.config import Config


class ChairmanA2A:
    def __init__(self, config: Config, event_bus=None):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=0.1,
            openai_api_key=config.llm.api_key,
            openai_api_base=config.llm.api_base,
        )
        self.event_bus = event_bus
        self.card = AgentCard(
            name="Chairman",
            description="The planner and router of the system. Decides which agent should act next.",
            version="1.0.0",
            capabilities={"skills": ["planning", "routing"]},
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[],
            url="http://localhost:8001/a2a/chairman",
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
        """Run Chairman in ReAct mode with real A2A agent calls."""
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

            logger.info(f"Chairman A2A: Received task: {message}")
            
            # Publish start event
            await self.publish_event("agent_start", "Formulating investigation plan...", task.context_id, status="thinking")

            # Create state for chairman_node
            state = {"messages": [HumanMessage(content=message)], "review_count": 0}

            # Run real chairman_node with A2A agent calls
            # NOTE: chairman_node calls other agents. We need to make sure those calls also propagate session_id.
            # But chairman_node uses `agent_map` which are initialized inside the node function in the original code.
            # We need to inject our event-aware agents into the node execution or modify chairman_node.
            # Given the complexity, let's modify chairman_node to accept an optional event_bus or session_id via state?
            # Or better, since we are in `ChairmanA2A`, we can reimplement the loop here to have full control over events.
            
            # Let's reimplement the loop here for better control and event publishing
            messages = state.get("messages", [])
            review_count = 0
            max_iterations = 5
            iteration = 0
            
            # Initialize A2A specialist agents with event bus
            from core.agents.macro import MacroA2A
            from core.agents.market import MarketA2A
            from core.agents.sentiment import SentimentA2A
            from core.agents.web_search import WebSearchA2A
            from core.agents.critic import CriticA2A
            
            # We use the same config and event bus
            agent_map = {
                "MacroDataInvestigator": MacroA2A(self.config, self.event_bus),
                "MarketDataInvestigator": MarketA2A(self.config, self.event_bus),
                "SentimentInvestigator": SentimentA2A(self.config, self.event_bus),
                "WebSearchInvestigator": WebSearchA2A(self.config, self.event_bus),
            }
            
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"Chairman: Iteration {iteration}/{max_iterations}")
                
                await self.publish_event("agent_status_change", f"Planning iteration {iteration}...", task.context_id, status="thinking", iteration=iteration)

                # Invoke Chairman LLM
                chairman_chain = create_chairman_chain(self.llm)
                result = await chairman_chain.ainvoke({"messages": messages})
                result.name = "Chairman"

                # Check for tool calls
                if not result.tool_calls:
                    
                    await self.publish_event("agent_message", "Investigation complete. Requesting final review.", task.context_id, status="speaking")
                    
                    # Chairman completes its work before routing to Critic
                    await self.publish_event("agent_end", "Chairman investigation complete", task.context_id, status="completed")
                    
                    # Call Critic
                    critic_agent = CriticA2A(self.config, self.event_bus)
                    critic_instruction = "Review all evidence gathered and provide a comprehensive final analysis."
                    
                    # Create task for Critic
                    critic_task = Task(
                        id=str(uuid.uuid4()),
                        context_id=task.context_id, # Pass same session ID
                        status=TaskStatus(state="submitted"),
                        history=[
                            Message(
                                messageId=str(uuid.uuid4()),
                                role=Role.user,
                                parts=[TextPart(text=critic_instruction + "\n\nCONTEXT:\n" + "\n".join([m.content for m in messages]))]
                            )
                        ]
                    )
                    
                    await self.publish_event("routing", "Routing to Critic", task.context_id, to="Critic", from_agent="Chairman")
                    critic_result = await critic_agent.run_task(critic_task)
                    critic_response = critic_result.get("response", "Critic synthesis unavailable")
                    
                    await self.publish_event("agent_end", "Chairman task completed", task.context_id, status="completed")
                    
                    return {
                        "response": critic_response,
                        "critic_synthesis": critic_response,
                        "next": "FINISH",
                        "steps": [],
                        "iterations": iteration
                    }

                # Execute tool call
                tool_call = result.tool_calls[0]
                if tool_call["name"] != "CallAgent":
                    logger.warning(f"Chairman: Unexpected tool call: {tool_call['name']}")
                    continue

                args = tool_call["args"]
                agent_name = args.get("agent")
                instruction = args.get("instruction")
                
                # Publish routing event
                await self.publish_event("routing", f"Routing to {agent_name}", task.context_id, to=agent_name, instruction=instruction)

                # Get specialist A2A agent
                specialist_agent = agent_map.get(agent_name)
                if not specialist_agent:
                    logger.error(f"Chairman: Unknown agent: {agent_name}")
                    await self.publish_event("error", f"Unknown agent: {agent_name}", task.context_id)
                    continue

                # Create A2A Task for specialist
                a2a_task = Task(
                    id=str(uuid.uuid4()),
                    context_id=task.context_id, # Pass same session ID
                    status=TaskStatus(state="submitted"),
                    history=[
                        Message(
                            messageId=str(uuid.uuid4()),
                            role=Role.user,
                            parts=[TextPart(text=instruction)],
                        )
                    ],
                )

                # Execute specialist via A2A
                # The specialist will publish its own events because we passed event_bus
                specialist_result = await specialist_agent.run_task(a2a_task)

                # Extract specialist's response
                specialist_response = specialist_result.get("response", "No response")
                specialist_steps = specialist_result.get("steps", [])

                # Format response with evidence
                evidence_summary = f"EVIDENCE from {agent_name}:\n{specialist_response}"
                if specialist_steps:
                    evidence_summary += f"\n\nTool calls made: {len(specialist_steps)}"

                # Add to conversation history
                messages.append(result)  # Chairman's decision
                messages.append(
                    ToolMessage(content=evidence_summary, tool_call_id=tool_call["id"])
                )
                
                # Chairman reactivates after receiving specialist's response
                await self.publish_event("agent_start", "Evaluating evidence and planning next step...", task.context_id, status="thinking")

            # Max iterations reached
            logger.warning("Chairman: Max iterations reached")
            await self.publish_event("error", "Max iterations reached", task.context_id)
            return {"error": "Max iterations reached"}

        except Exception as e:
            logger.error(f"A2A Chairman Error: {e}")
            import traceback
            traceback.print_exc()
            if task and task.context_id:
                await self.publish_event("error", str(e), task.context_id)
            return {"error": str(e)}


def setup_a2a(app: FastAPI, config: Config):
    """Setup Chairman A2A agent."""
    agent = ChairmanA2A(config)
    router = APIRouter(prefix="/a2a", tags=["A2A"])

    @router.get("/chairman/.well-known/agent.json", tags=[agent.card.name])
    async def get_card():
        return agent.card.dict()

    @router.post("/chairman/run", tags=[agent.card.name])
    async def run_agent(request: Request):
        data = await request.json()
        # Note: In a real A2A server, we would parse 'data' into a Task object
        # For now, we assume the input is a raw JSON that matches Task schema or we construct it
        # But since we are using the SDK types, we should try to parse it
        try:
            task = Task(**data)
        except:
            # Fallback for simple testing if needed, or just error out
            # For this specific codebase, let's assume standard A2A request structure
            task = Task(**data)

        return await agent.run_task(task)

    app.include_router(router)


if __name__ == "__main__":
    import asyncio
    from core.config import get_config
    import uuid

    async def main():
        try:
            # 1. Load Config
            config = get_config()
            logger.info("Config loaded.")

            # 2. Initialize Agent
            chairman = ChairmanA2A(config)
            logger.info("Chairman initialized.")

            # 3. Create Test Task
            # Chairman expects a message that implies a need for planning or routing
            test_message = (
                "Analyze the stock price of Apple (AAPL) and its recent news sentiment."
            )

            task = A2ATask(
                id=str(uuid.uuid4()),
                context_id=str(uuid.uuid4()),
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
            result = await chairman.run_task(task)

            # 5. Print Result
            import json

            print("\n--- Result ---")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # Print Critic synthesis separately if available
            if result.get("critic_synthesis"):
                print("\n=== CRITIC FINAL SYNTHESIS ===")
                print(result["critic_synthesis"])

        except Exception as e:
            logger.error(f"Test failed: {e}")
            import traceback

            traceback.print_exc()

    asyncio.run(main())
