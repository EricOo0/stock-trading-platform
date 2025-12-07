import requests
import logging
from typing import Dict, List, Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

class MemoryClient:
    """Client for the Data-First Memory System Service"""
    
    def __init__(self, base_url: str = "http://localhost:10000", agent_id: str = "default_agent"):
        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id

    def add_memory(self, content: Any, role: str = "user", metadata: Optional[Dict] = None) -> bool:
        """
        Add memory to the system.
        
        Args:
            content: The content string or event logic.
            role: The role (user/agent/system).
            metadata: Additional metadata.
        """
        try:
            payload = {
                "agent_id": self.agent_id,
                "content": content,
                "metadata": {
                    "role": role,
                    **(metadata or {})
                }
            }
            
            response = requests.post(f"{self.base_url}/api/v1/memory/add", json=payload, timeout=5)
            response.raise_for_status()
            logger.info(f"Memory added for {self.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return False

    def get_context(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve cognitive context for a query.
        """
        try:
            payload = {
                "agent_id": self.agent_id,
                "query": query,
                "session_id": session_id
            }
            
            response = requests.post(f"{self.base_url}/api/v1/memory/context", json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "success":
                return data["context"]
            return {}
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return {}

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            response = requests.get(f"{self.base_url}/api/v1/memory/stats", params={"agent_id": self.agent_id}, timeout=5)
            response.raise_for_status()
            return response.json().get("stats", {})
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
