"""Streaming implementation of Chairman A2A agent for real-time ReAct loop."""

import asyncio
from typing import Dict, Any, AsyncGenerator, Optional
from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from core.state import AgentState
from core.prompts import CHAIRMAN_SYSTEM_PROMPT
from core.schema import CallAgent
from a2a.types import Task, TaskStatus, Message, Role, TextPart
from core.config import Config


class StreamingChairmanA2A:
    """Streaming Chairman A2A agent that yields events in real-time."""

    def __init__(self, config: Config):
        self.llm = ChatOpenAI(
            model=config.llm.model,
            temperature=0.0,  # Deterministic planning
            openai_api_key=config.llm.api_key,
            openai_api_base=config.llm.api_base,
        )

        # Create chairman chain with tool binding
        self.chairman_chain = self._create_chairman_chain()

        self.card = {
            "name": "Chairman",
            "description": "The planner and router of the system. Decides which agent should act next.",
            "version": "2.0.0",
            "capabilities": {"skills": ["planning", "routing", "streaming"]},
            "topics": ["stock", "finance"],
        }

    def _create_chairman_chain(self):
        """Create the chairman chain with CallAgent tool binding."""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", CHAIRMAN_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return prompt | self.llm.bind_tools([CallAgent], tool_choice="auto")

    async def stream_task(self, task: Task) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream the Chairman ReAct loop with real-time events."""
        try:
            # Extract message from history
            message = ""
            if task.history:
                last_msg = task.history[-1]
                for part in last_msg.parts:
                    if part.root.kind == "text":
                        message += part.root.text

            if not message:
                yield {
                    "type": "error",
                    "content": "No message provided in task history",
                }
                return

            logger.info(f"Streaming Chairman task: {message}")

            # Initial state
            messages = [HumanMessage(content=message)]
            review_count = 0
            max_iterations = 5
            iteration = 0

            # Yield start event
            yield {
                "type": "agent_start",
                "agent": "Chairman",
                "status": "thinking",
                "message": "Starting investigation planning...",
                "iteration": iteration,
            }

            while iteration < max_iterations:
                iteration += 1
                logger.info(
                    f"Chairman streaming iteration {iteration}/{max_iterations}"
                )

                # Yield thinking event
                yield {
                    "type": "agent_status_change",
                    "agent": "Chairman",
                    "status": "thinking",
                    "message": f"Analyzing situation (iteration {iteration})...",
                    "iteration": iteration,
                }

                # Build context for Chairman
                context = self._build_chairman_context(messages, iteration)

                # Invoke Chairman LLM
                result = await self.chairman_chain.ainvoke({"messages": context})
                result.name = "Chairman"

                # Check for tool calls
                if not result.tool_calls:
                    # No more tool calls, task complete
                    yield {
                        "type": "agent_status_change",
                        "agent": "Chairman",
                        "status": "speaking",
                        "message": "Investigation complete",
                        "iteration": iteration,
                    }

                    yield {
                        "type": "agent_message",
                        "agent": "Chairman",
                        "content": result.content or "Investigation planning complete",
                        "iteration": iteration,
                    }

                    yield {
                        "type": "agent_end",
                        "agent": "Chairman",
                        "status": "completed",
                        "message": f"Planning completed after {iteration} iterations",
                        "iterations": iteration,
                    }
                    break

                # Execute tool call
                tool_call = result.tool_calls[0]
                if tool_call["name"] != "CallAgent":
                    logger.warning(
                        f"Chairman: Unexpected tool call: {tool_call['name']}"
                    )
                    continue

                args = tool_call["args"]
                agent_name = args.get("agent")
                instruction = args.get("instruction")

                # Yield Chairman's reasoning
                if result.content and result.content.strip():
                    yield {
                        "type": "agent_message",
                        "agent": "Chairman",
                        "content": result.content,
                        "iteration": iteration,
                    }

                # Yield routing event
                yield {
                    "type": "routing",
                    "from": "Chairman",
                    "to": agent_name,
                    "message": f"Routing to {agent_name} for investigation",
                    "instruction": instruction,
                    "iteration": iteration,
                }

                # Add Chairman's decision to messages
                messages.append(result)

                # Yield agent start event for specialist
                yield {
                    "type": "agent_start",
                    "agent": agent_name,
                    "status": "thinking",
                    "message": f"Received instruction: {instruction[:100]}...",
                    "iteration": iteration,
                }

                # For now, we'll yield the instruction and let the caller handle execution
                # This allows the Chairman to continue streaming while specialist executes
                yield {
                    "type": "tool_call",
                    "agent": "Chairman",
                    "tool_name": "CallAgent",
                    "tool_input": args,
                    "tool_output": f"Routing to {agent_name}",
                    "iteration": iteration,
                }

                # Add tool result to conversation (placeholder - actual execution happens externally)
                tool_result = (
                    f"EVIDENCE from {agent_name}: Execution completed externally"
                )
                messages.append(
                    ToolMessage(content=tool_result, tool_call_id=tool_call["id"])
                )

                # Small delay to simulate processing time
                await asyncio.sleep(0.1)

            if iteration >= max_iterations:
                yield {
                    "type": "error",
                    "content": f"Maximum iterations ({max_iterations}) reached",
                    "phase": "chairman_loop",
                }

        except Exception as e:
            logger.error(f"Streaming Chairman Error: {e}")
            yield {"type": "error", "content": f"Chairman streaming error: {str(e)}"}

    def _build_chairman_context(self, messages: list, iteration: int) -> list:
        """Build context for Chairman decision making."""
        # For streaming, we return the messages as-is
        # The context building logic is handled in the main chain
        return messages

    async def run_task(self, task: Task) -> dict:
        """Legacy non-streaming method for compatibility."""
        # Collect all streaming events
        events = []
        async for event in self.stream_task(task):
            events.append(event)

        # Extract final result
        final_message = ""
        iterations = 0

        for event in events:
            if (
                event.get("type") == "agent_message"
                and event.get("agent") == "Chairman"
            ):
                final_message = event.get("content", "")
            if event.get("type") == "agent_end" and event.get("agent") == "Chairman":
                iterations = event.get("iterations", 0)

        return {
            "response": final_message or "Chairman completed task",
            "steps": events,
            "iterations": iterations,
            "next": "FINISH",
        }


def create_streaming_chairman_agent(config: Config):
    """Factory function to create streaming chairman agent."""
    return StreamingChairmanA2A(config)
