"""Multi-Agent implementation using LangGraph."""

from typing import Any, Dict, List, Optional
from loguru import logger

from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from core.config import Config
from core.graph import create_graph
from core.memory import ConversationMemory
from utils.exceptions import LLMError, AgentException


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
        logger.info("Stock Analysis Multi-Agent System initialized successfully")
    
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
        self,
        query: str,
        memory: Optional[ConversationMemory] = None
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
            
            inputs = {
                "messages": [HumanMessage(content=query)]
            }
            
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
                if not output and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    logger.info("Last message is a tool call with empty content. Looking for previous meaningful message.")
                    # Iterate backwards to find the last message with content
                    for msg in reversed(final_messages[:-1]):
                        if msg.content and msg.type == "ai":
                            output = msg.content
                            logger.info(f"Found previous content from {getattr(msg, 'name', 'Unknown')}")
                            break
            else:
                output = "No response generated."
            
            # Intermediate steps are essentially the messages in the middle
            # We can format them for the frontend if needed
            intermediate_steps = []
            for msg in final_messages[:-1]:
                intermediate_steps.append({
                    "agent": getattr(msg, "name", "Unknown"),
                    "content": msg.content,
                    "type": msg.type
                })
            
            response = {
                "output": output,
                "intermediate_steps": intermediate_steps,
                "success": True
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
                "error": str(e)
            }

    async def stream_run(self, query: str):
        """
        Stream the agent execution with a user query.
        Yields structured events:
        - agent_start: Agent starts working (Thinking)
        - agent_message: Agent outputs text (Speaking)
        - routing: System routing event
        - agent_end: Agent finishes
        """
        try:
            logger.info(f"Streaming query: {query}")
            from langchain_core.messages import HumanMessage, ToolMessage
            
            inputs = {
                "messages": [HumanMessage(content=query)]
            }
            
            config = {"recursion_limit": 50}  # Increased from 20 to 50
            
            # 1. Receptionist Start (Thinking)
            yield {
                "type": "agent_start",
                "agent": "Receptionist",
                "status": "thinking",
                "message": "Analyzing user intent..."
            }
            
            # Use astream to get updates
            async for event in self.graph.astream(inputs, config=config, stream_mode="updates"):
                for node_name, state_update in event.items():
                    
                    # Extract messages from the update
                    messages = state_update.get("messages", [])
                    if not isinstance(messages, list):
                        messages = [messages]
                    
                    # --- Chairman Logic ---
                    if node_name == "Chairman":
                        next_agent = state_update.get("next")
                        
                        # Case 1: Chairman is routing to an agent (executing a step)
                        if next_agent and next_agent not in ["FINISH", "Critic"]:
                            # Extract instruction from messages
                            instruction = "Executing step..."
                            if messages:
                                # The last message should be the instruction
                                for msg in reversed(messages):
                                    if isinstance(msg, HumanMessage):
                                        instruction = msg.content
                                        break
                            
                            # Emit routing event
                            yield {
                                "type": "routing",
                                "from": "Chairman",
                                "to": next_agent,
                                "message": f"Routing to {next_agent}...",
                                "instruction": instruction
                            }
                            
                            # Trigger next agent Thinking (THIS is the key fix!)
                            yield {
                                "type": "agent_start",
                                "agent": next_agent,
                                "status": "thinking",
                                "message": f"Received instruction: {instruction[:50]}..."
                            }
                        
                        # Case 2: Chairman is finishing (routing to Critic)
                        elif next_agent == "FINISH":
                             yield {
                                "type": "routing",
                                "from": "Chairman",
                                "to": "Critic",
                                "message": "Investigation complete. Routing to Critic...",
                                "instruction": "Review evidence and synthesize answer."
                            }
                             yield {
                                "type": "agent_start",
                                "agent": "Critic",
                                "status": "thinking",
                                "message": "Reviewing evidence..."
                            }

                    # --- Specialist Logic ---
                    elif node_name in ["MacroDataInvestigator", "MarketDataInvestigator", "SentimentInvestigator", "WebSearchInvestigator"]:
                        # Check if the agent is done (no more tool calls)
                        # This indicates it will route back to Chairman
                        is_done = False
                        has_tool_calls = False
                        
                        if messages:
                            last_msg = messages[-1]
                            has_tool_calls = hasattr(last_msg, 'tool_calls') and last_msg.tool_calls
                            
                            # Case 1: Agent has tool calls (executing tools)
                            if has_tool_calls:
                                # Show what tools are being executed
                                tool_names = [tc['name'] for tc in last_msg.tool_calls]
                                tool_desc = ", ".join(tool_names)
                                
                                # If there's content, show it (agent's reasoning)
                                if last_msg.content and last_msg.content.strip():
                                    yield {
                                        "type": "agent_message",
                                        "agent": node_name,
                                        "content": last_msg.content
                                    }
                                
                                # Always show tool execution
                                yield {
                                    "type": "agent_message",
                                    "agent": node_name,
                                    "content": f"🔧 Executing: {tool_desc}"
                                }
                            
                            # Case 2: Agent has content but no tool calls (final conclusion)
                            elif last_msg.content and last_msg.content.strip():
                                is_done = True
                                yield {
                                    "type": "agent_message",
                                    "agent": node_name,
                                    "content": last_msg.content
                                }
                        
                        # Only predict Chairman thinking if the agent is truly done
                        if is_done:
                            yield {
                                "type": "agent_start",
                                "agent": "Chairman",
                                "status": "thinking",
                                "message": "Reviewing step results..."
                            }

                    # --- Receptionist Logic ---
                    elif node_name == "Receptionist":
                        # Receptionist finished, speaks the brief
                        brief = state_update.get("research_brief", "")
                        if brief:
                            yield {
                                "type": "agent_message",
                                "agent": "Receptionist",
                                "content": brief
                            }
                        
                        # Route to Chairman
                        yield {
                            "type": "agent_start",
                            "agent": "Chairman",
                            "status": "thinking",
                            "message": "Formulating investigation plan..."
                        }

                    # --- Critic Logic ---
                    elif node_name == "Critic":
                        # Critic finished, speaks final answer
                        if messages:
                            yield {
                                "type": "agent_message",
                                "agent": "Critic",
                                "content": messages[-1].content
                            }
                        yield {
                            "type": "agent_end",
                            "agent": "Critic"
                        }

        except Exception as e:
            logger.error(f"Error streaming agent: {e}")
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
            "WebSearchInvestigator"
        ]
