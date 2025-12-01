"""A2A Client for calling A2A agents directly via class instances."""

import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from loguru import logger
import uuid
from dataclasses import dataclass

# Import A2A agent classes
from core.agents.chairman import ChairmanA2A
from core.agents.critic import CriticA2A
from core.agents.macro import MacroA2A
from core.agents.market import MarketA2A
from core.agents.sentiment import SentimentA2A
from core.agents.web_search import WebSearchA2A

# Import A2A types
from a2a.types import Task, TaskStatus, Message, Role, TextPart


@dataclass
class A2ATaskResponse:
    """A2A Task response structure."""

    response: str
    steps: list = None
    error: Optional[str] = None
    success: bool = True


class A2AAgentClient:
    """Client for calling A2A agents directly via class instances."""

    def __init__(self, config):
        """Initialize A2A agent client.

        Args:
            config: Agent configuration
        """
        self.config = config
        self._agents: Dict[str, Any] = {}
        
        # Initialize EventBus
        from core.bus import get_event_bus
        self.event_bus = get_event_bus()
        
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all A2A agent instances."""
        try:
            from core.agents.receptionist import ReceptionistA2A
            self._agents["receptionist"] = ReceptionistA2A(self.config, self.event_bus)
            self._agents["chairman"] = ChairmanA2A(self.config, self.event_bus)
            self._agents["critic"] = CriticA2A(self.config, self.event_bus)
            self._agents["macrodatainvestigator"] = MacroA2A(self.config, self.event_bus)
            self._agents["marketdatainvestigator"] = MarketA2A(self.config, self.event_bus)
            self._agents["sentimentinvestigator"] = SentimentA2A(self.config, self.event_bus)
            self._agents["websearchinvestigator"] = WebSearchA2A(self.config, self.event_bus)

            logger.info("A2A agents initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize A2A agents: {e}")
            raise

    def _create_task(self, message: str, session_id: Optional[str] = None) -> Task:
        """Create A2A task from message.

        Args:
            message: User message
            session_id: Optional session ID

        Returns:
            A2A Task object
        """
        return Task(
            id=str(uuid.uuid4()),
            context_id=session_id or str(uuid.uuid4()),
            status=TaskStatus(state="submitted"),
            history=[
                Message(
                    messageId=str(uuid.uuid4()),
                    role=Role.user,
                    parts=[TextPart(text=message)],
                )
            ],
        )

    async def call_agent(
        self, agent_name: str, message: str, session_id: Optional[str] = None
    ) -> A2ATaskResponse:
        """Call an A2A agent directly.

        Args:
            agent_name: Name of the A2A agent
            message: Message to send to the agent
            session_id: Optional session ID for conversation continuity

        Returns:
            A2ATaskResponse with agent's response
        """
        try:
            # Normalize agent name
            agent_key = agent_name.lower().replace(" ", "")

            # Get agent instance
            agent = self._agents.get(agent_key)
            if not agent:
                logger.error(f"A2A agent not found: {agent_name} (key: {agent_key})")
                return A2ATaskResponse(
                    response="", error=f"Agent {agent_name} not found", success=False
                )

            # Create task
            task = self._create_task(message, session_id)

            logger.info(f"Calling A2A agent {agent_name} directly with message: {message[:100]}...")

            # Call agent
            result = await agent.run_task(task)

            # Handle response format
            if isinstance(result, dict):
                if "error" in result:
                    return A2ATaskResponse(
                        response="", error=result["error"], success=False
                    )
                elif "response" in result:
                    logger.info(f"A2A agent {agent_name} completed successfully with {len(result.get('steps', []))} steps")
                    return A2ATaskResponse(
                        response=result["response"],
                        steps=result.get("steps", []),
                        success=True,
                    )
                else:
                    # Fallback - treat entire result as response
                    response_text = str(result.get("response", ""))
                    if not response_text:
                        response_text = json.dumps(result, ensure_ascii=False)
                    logger.info(f"A2A agent {agent_name} returned fallback response: {response_text[:100]}...")
                    return A2ATaskResponse(response=response_text, success=True)
            else:
                # Handle non-dict responses
                logger.info(f"A2A agent {agent_name} returned non-dict response")
                return A2ATaskResponse(response=str(result), success=True)

        except Exception as e:
            logger.error(f"Error calling A2A agent {agent_name}: {e}")
            return A2ATaskResponse(
                response="", error=f"Agent error: {str(e)}", success=False
            )

    async def stream_agent(
        self, agent_name: str, message: str, session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream call an A2A agent with detailed progress events.

        Args:
            agent_name: Name of the A2A agent
            message: Message to send to the agent
            session_id: Optional session ID

        Yields:
            Stream events from the agent with detailed progress info
        """
        # Start event with detailed info
        yield {
            "type": "agent_start",
            "agent": agent_name,
            "status": "thinking",
            "message": f"{agent_name} is analyzing the request...",
            "timestamp": asyncio.get_event_loop().time(),
            "session_id": session_id,
        }

        # Small delay to simulate thinking
        await asyncio.sleep(0.3)

        # Get actual response
        response = await self.call_agent(agent_name, message, session_id)

        if response.success:
            # Thinking complete, start speaking
            yield {
                "type": "agent_status_change",
                "agent": agent_name,
                "status": "speaking",
                "message": f"{agent_name} is responding...",
            }

            # Agent message with content
            yield {
                "type": "agent_message",
                "agent": agent_name,
                "content": response.response,
                "steps": response.steps or [],
                "step_count": len(response.steps) if response.steps else 0,
            }

            # If there are tool execution steps, yield them as separate events
            if response.steps:
                for i, step in enumerate(response.steps):
                    yield {
                        "type": "tool_call",
                        "agent": agent_name,
                        "tool_name": step.get("tool", "unknown"),
                        "tool_input": step.get("input", {}),
                        "tool_output": step.get("output", ""),
                        "step_index": i + 1,
                        "total_steps": len(response.steps),
                    }
        else:
            yield {
                "type": "error",
                "content": response.error or "Unknown error",
                "agent": agent_name,
            }

        # End event
        yield {
            "type": "agent_end",
            "agent": agent_name,
            "status": "idle",
            "message": f"{agent_name} completed task",
        }

    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent card information.

        Args:
            agent_name: Name of the A2A agent

        Returns:
            Agent card data or None if not found
        """
        try:
            agent_key = agent_name.lower().replace(" ", "")
            agent = self._agents.get(agent_key)

            if agent and hasattr(agent, "card"):
                # Convert card to dict
                card_data = {}
                if hasattr(agent.card, "dict"):
                    card_data = agent.card.dict()
                else:
                    # Manual conversion
                    card_data = {
                        "name": getattr(agent.card, "name", agent_name),
                        "description": getattr(agent.card, "description", ""),
                        "version": getattr(agent.card, "version", "1.0.0"),
                        "capabilities": getattr(agent.card, "capabilities", {}),
                        "url": getattr(agent.card, "url", ""),
                        "topics": getattr(agent.card, "topics", []),
                    }
                return card_data

            return None

        except Exception as e:
            logger.error(f"Error getting agent info for {agent_name}: {e}")
            return None


# Singleton instance
_a2a_client: Optional[A2AAgentClient] = None


def get_a2a_agent_client(config=None) -> A2AAgentClient:
    """Get singleton A2A agent client instance."""
    global _a2a_client
    if _a2a_client is None:
        if config is None:
            from core.config import get_config

            config = get_config()
        _a2a_client = A2AAgentClient(config)
    return _a2a_client


async def call_a2a_agent_direct(
    agent_name: str, message: str, session_id: Optional[str] = None, config=None
) -> A2ATaskResponse:
    """Convenience function to call A2A agent directly."""
    client = get_a2a_agent_client(config)
    return await client.call_agent(agent_name, message, session_id)
