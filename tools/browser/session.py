import os
import requests
import logging
from typing import Optional, Dict, Any
from tools.config import config

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages Steel.dev browser sessions via raw HTTP API (Reliable)."""
    
    API_URL = "https://api.steel.dev"
    
    def __init__(self):
        self.api_key = config.get_api_key("steel")
        if not self.api_key:
            logger.warning("Steel API key not found in config.")
            
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def create_session(self, release_timeout: int = 300) -> Optional[Dict[str, Any]]:
        """
        Creates a new browser session.
        """
        if not self.api_key:
            return None
            
        try:
            url = f"{self.API_URL}/v1/sessions"
            # Using basic default options for compatibility
            payload = {
                "releaseTimeout": release_timeout,
                "proxy": True,
                "solveCaptcha": True
            }
            
            resp = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"Created Steel Session: {data.get('id')}")
                return {
                    "session_id": data.get("id"),
                    "websocket_url": f"wss://connect.steel.dev?apiKey={self.api_key}&sessionId={data.get('id')}",
                    "debug_url": data.get("debugUrl"),
                    "session_viewer_url": data.get("sessionViewerUrl"),
                    "status": "live"
                }
            else:
                logger.error(f"Failed to create session: {resp.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None

    def release_session(self, session_id: str) -> bool:
        """Releases/Closes a Steel.dev session."""
        try:
            url = f"{self.API_URL}/v1/sessions/{session_id}/release"
            resp = requests.post(url, headers=self._get_headers(), timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Error releasing session {session_id}: {e}")
            return False

session_manager = SessionManager()
