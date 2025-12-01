import asyncio
from typing import Dict, Any, AsyncGenerator, Optional
from loguru import logger
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Event:
    """Standard event structure for the Data Bus."""
    type: str
    session_id: str
    agent: str
    content: Optional[str] = None
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

class EventBus:
    """
    Singleton Event Bus for decoupling agent execution from event streaming.
    Agents publish events here, and the API layer subscribes to stream them to the client.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._channels = {}  # session_id -> asyncio.Queue
        return cls._instance

    def get_channel(self, session_id: str) -> asyncio.Queue:
        """Get or create a channel for a session."""
        if session_id not in self._channels:
            self._channels[session_id] = asyncio.Queue()
        return self._channels[session_id]

    async def publish(self, event: Event):
        """Publish an event to a specific session channel."""
        if not event.session_id:
            logger.warning(f"EventBus: Event {event.type} missing session_id, dropping.")
            return

        channel = self.get_channel(event.session_id)
        await channel.put(event)
        logger.debug(f"EventBus: Published {event.type} to {event.session_id}")

    async def subscribe(self, session_id: str) -> AsyncGenerator[Event, None]:
        """
        Subscribe to events for a session.
        Yields events as they arrive.
        """
        channel = self.get_channel(session_id)
        try:
            while True:
                event = await channel.get()
                yield event
                channel.task_done()
                
                # Check for termination event
                if event.type == "system_end" or (event.type == "agent_end" and event.agent == "System"):
                    break
        except asyncio.CancelledError:
            logger.info(f"EventBus: Subscription cancelled for {session_id}")
            # Cleanup could happen here if needed
        finally:
            # Optional: Remove channel if empty and unused
            pass

    def clear_channel(self, session_id: str):
        """Clear a channel (e.g., on session end)."""
        if session_id in self._channels:
            del self._channels[session_id]

# Global instance
_event_bus = EventBus()

def get_event_bus() -> EventBus:
    return _event_bus
