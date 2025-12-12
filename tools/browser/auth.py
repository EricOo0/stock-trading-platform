import os
import json
import logging
from typing import Optional, Dict
from playwright.async_api import BrowserContext

logger = logging.getLogger(__name__)

class AuthManager:
    """Manages browser authentication states (cookies/storage)."""
    
    ROOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "auth")
    
    def __init__(self):
        os.makedirs(self.ROOT_DIR, exist_ok=True)
    
    def get_auth_path(self, site_name: str) -> str:
        """Returns the file path for a site's auth state."""
        return os.path.join(self.ROOT_DIR, f"{site_name}.json")
    
    async def save_state(self, context: BrowserContext, site_name: str):
        """Saves the current browser context state to disk."""
        path = self.get_auth_path(site_name)
        try:
            state = await context.storage_state(path=path)
            logger.info(f"Saved auth state for {site_name} to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save auth state: {e}")
            return False

    def get_state_path_if_exists(self, site_name: str) -> Optional[str]:
        """Returns the auth file path if it exists."""
        path = self.get_auth_path(site_name)
        return path if os.path.exists(path) else None

auth_manager = AuthManager()
