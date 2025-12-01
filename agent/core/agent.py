"""Multi-Agent implementation using A2A protocol."""

from typing import Any, Dict, List, Optional
from loguru import logger
import asyncio

from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from core.config import Config
from core.graph import create_graph
from core.memory import ConversationMemory
from core.a2a_client import get_a2a_agent_client, A2AAgentClient
from utils.exceptions import LLMError, AgentException
import uuid


class StockAnalysisAgent:
    """
    Multi-Agent System for stock analysis.

    This agent uses a LangGraph-based Supervisor-Worker architecture to:
    1. Analyze user queries via a Business Manager (Supervisor).
    2. Route tasks to specialized agents (Macro, Market, Sentiment, Search).
    3. Collaborate and iterate to provide a comprehensive answer.
    """

    def __init__(self, config: Config):
        """
        Initialize the stock analysis agent.

        Args:
            config: Agent configuration
        """
        self.config = config
        self.graph: CompiledStateGraph = self._init_graph()
        self.a2a_client: A2AAgentClient = get_a2a_agent_client(config)
        logger.info(
            "Stock Analysis Multi-Agent System initialized successfully with A2A support"
        )

    def _init_graph(self) -> CompiledStateGraph:
        """
        Initialize the LangGraph workflow.

        Returns:
            CompiledGraph instance
        """
        try:
            graph = create_graph(self.config)
            logger.info("Multi-Agent Graph created successfully")
            return graph
        except Exception as e:
            logger.error(f"Failed to create agent graph: {e}")
            raise AgentException(f"Failed to create agent graph: {e}")

    async def run(
        self, query: str, memory: Optional[ConversationMemory] = None
    ) -> Dict[str, Any]:
        """
        Run the agent with a user query.

        Args:
            query: User query
            memory: Optional conversation memory

        Returns:
            Dict with response and intermediate steps
        """
        try:
            logger.info(f"Processing query: {query}")

            # Prepare chat history
            # In LangGraph, we usually pass the full history as 'messages'
            # But here we might need to adapt based on how ConversationMemory works.
            # For now, we'll just pass the new query and let the graph handle its internal state.
            # Ideally, we should load history from memory into the graph state.

            messages = []
            if memory:
                # Convert memory history to LangChain messages if needed
                # For simplicity, we'll just start with the user's query
                # In a production app, we'd map memory.get_chat_history() to BaseMessage objects
                pass

            from langchain_core.messages import HumanMessage

            inputs = {"messages": [HumanMessage(content=query)]}

            # Run graph
            # We use ainvoke to run the graph
            # The config recursion_limit controls the maximum number of steps
            config = {"recursion_limit": 20}

            result = await self.graph.ainvoke(inputs, config=config)

            # Extract response
            # The result is the final state. 'messages' contains the full history.
            # The last message should be the final answer from the Business Manager.
            final_messages = result.get("messages", [])
            if final_messages:
                last_message = final_messages[-1]
                output = last_message.content

                # If the last message is a tool call (e.g. Supervisor routing to FINISH),
                # it might have empty content. In that case, we should look at the previous message
                # which likely contains the actual answer from a worker.
                if (
                    not output
                    and hasattr(last_message, "tool_calls")
                    and last_message.tool_calls
                ):
                    logger.info(
                        "Last message is a tool call with empty content. Looking for previous meaningful message."
                    )
                    # Iterate backwards to find the last message with content
                    for msg in reversed(final_messages[:-1]):
                        if msg.content and msg.type == "ai":
                            output = msg.content
                            logger.info(
                                f"Found previous content from {getattr(msg, 'name', 'Unknown')}"
                            )
                            break
            else:
                output = "No response generated."

            # Intermediate steps are essentially the messages in the middle
            # We can format them for the frontend if needed
            intermediate_steps = []
            for msg in final_messages[:-1]:
                intermediate_steps.append(
                    {
                        "agent": getattr(msg, "name", "Unknown"),
                        "content": msg.content,
                        "type": msg.type,
                    }
                )

            response = {
                "output": output,
                "intermediate_steps": intermediate_steps,
                "success": True,
            }

            # Update memory
            if memory:
                memory.add_message("user", query)
                memory.add_message("assistant", output)

            logger.info("Query processed successfully")
            return response

        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return {
                "output": f"抱歉，处理您的请求时出现了错误：{str(e)}",
                "intermediate_steps": [],
                "success": False,
                "error": str(e),
            }

    async def stream_run(self, query: str):
        """
        Stream the agent execution with a user query using A2A protocol.
        Implements real-time ReAct loop with detailed progress tracking via EventBus.
        """
        try:
            logger.info(f"Streaming query via A2A: {query}")
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            
            # Get EventBus
            from core.bus import get_event_bus
            event_bus = get_event_bus()
            
            # Start the agent execution in the background
            # We use asyncio.create_task to run it without blocking the generator
            async def run_pipeline():
                from core.bus import Event  # Import Event here
                try:
                    # Call Receptionist via A2A
                    receptionist_response = await self.a2a_client.call_agent(
                        "receptionist", query, session_id
                    )
                    
                    if not receptionist_response.success:
                        await event_bus.publish(Event(
                            type="error", 
                            session_id=session_id, 
                            agent="System", 
                            content=f"Receptionist failed: {receptionist_response.error}"
                        ))
                        return

                    # 2. Chairman
                    chairman_msg = f"User Query: {query}\n\nResearch Brief: {receptionist_response.response}"
                    
                    chairman_response = await self.a2a_client.call_agent(
                        "chairman", chairman_msg, session_id
                    )
                    
                    if not chairman_response.success:
                         await event_bus.publish(Event(
                            type="error", 
                            session_id=session_id, 
                            agent="System", 
                            content=f"Chairman failed: {chairman_response.error}"
                        ))
                         return
                         
                    # Done
                    await event_bus.publish(Event(
                        type="system_end",
                        session_id=session_id,
                        agent="System",
                        content="Workflow completed"
                    ))
                    
                except Exception as e:
                    logger.error(f"Pipeline Error: {e}")
                    import traceback
                    traceback.print_exc()
                    await event_bus.publish(Event(
                        type="error",
                        session_id=session_id,
                        agent="System",
                        content=str(e)
                    ))

            # Launch background task
            asyncio.create_task(run_pipeline())
            
            # Subscribe and yield events
            from core.bus import Event
            async for event in event_bus.subscribe(session_id):
                # Convert Event object to dict for frontend
                yield {
                    "type": event.type,
                    "agent": event.agent,
                    "content": event.content,
                    "timestamp": event.timestamp,
                    **event.metadata
                }
                
        except Exception as e:
            logger.error(f"Error streaming A2A agent: {e}")
            yield {
                "type": "error",
                "content": f"Error: {str(e)}"
            }


    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool names.

        Returns:
            List of tool names
        """
        # In the graph architecture, tools are internal to workers.
        # We can return the worker names or just a static list.
        return [
            "MacroDataInvestigator",
            "MarketDataInvestigator",
            "SentimentInvestigator",
            "WebSearchInvestigator",
        ]
