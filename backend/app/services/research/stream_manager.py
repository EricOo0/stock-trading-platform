import asyncio
import logging
from typing import List, Dict
from sse_starlette.sse import ServerSentEvent

logger = logging.getLogger(__name__)


class StreamManager:
    def __init__(self):
        # job_id -> List[asyncio.Queue]
        self.listeners: Dict[str, List[asyncio.Queue]] = {}

    async def connect(self, job_id: str):
        queue = asyncio.Queue()
        if job_id not in self.listeners:
            self.listeners[job_id] = []
        self.listeners[job_id].append(queue)

        # Send initial connection event
        await queue.put(ServerSentEvent(event="status", data="connected"))
        logger.info(f"New listener connected to job {job_id}")

        try:
            while True:
                # Wait for new message
                message = await queue.get()
                yield message
        except asyncio.CancelledError:
            logger.info(f"Listener disconnected from job {job_id}")
        finally:
            if job_id in self.listeners:
                self.listeners[job_id].remove(queue)
                if not self.listeners[job_id]:
                    del self.listeners[job_id]

    async def push_event(self, job_id: str, event_type: str, data: str):
        """
        Push an event to all active listeners for a given job.
        """
        if job_id in self.listeners:
            listeners = self.listeners[job_id]
            # Create SSE object
            sse_event = ServerSentEvent(event=event_type, data=data)

            # Broadcast to all queues
            for queue in listeners:
                await queue.put(sse_event)


stream_manager = StreamManager()
