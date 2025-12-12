import os
import logging
from typing import Optional, Dict, Any
from backend.infrastructure.config.loader import config
from steel import Steel

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages Steel.dev browser sessions using the official SDK."""
    
    def __init__(self):
        _key = config.get_api_key("steel")
        self.client = None
        
        if not _key:
            logger.warning("Steel API key not found in config.")
            return

        try:
            self.client = Steel(steel_api_key=_key)
        except Exception as e:
            logger.error(f"Failed to initialize Steel client: {e}")

    @property
    def api_key(self) -> str:
        return self.client.steel_api_key if self.client else ""

    def create_session(self, release_timeout: int = 300) -> Optional[Dict[str, Any]]:
        """
        Creates a new browser session via Steel SDK.
        """
        if not self.client:
            logger.error("Steel client not initialized.")
            return None
            
        try:
            session = self.client.sessions.create()
            logger.info(f"Created Steel Session: {session.id}")
            
            return {
                "session_id": session.id,
                "websocket_url": f"wss://connect.steel.dev?apiKey={self.api_key}&sessionId={session.id}",
                "debug_url": getattr(session, 'debug_url', None),
                "session_viewer_url": getattr(session, 'session_viewer_url', None),
                "status": getattr(session, 'status', 'live')
            }
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None

    def release_session(self, session_id: str) -> bool:
        """Releases/Closes a Steel.dev session."""
        if not self.client:
            return False
            
        try:
            self.client.sessions.release(session_id)
            logger.info(f"Released session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error releasing session {session_id}: {e}")
            return False

session_manager = SessionManager()
