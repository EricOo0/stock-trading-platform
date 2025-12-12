import asyncio
import logging
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from .session import session_manager

logger = logging.getLogger(__name__)

class BrowserEngine:
    """
    High-level browser automation engine backed by Steel.dev and Playwright.
    """
    
    _instance = None
    _browser: Optional[Browser] = None
    _playwright = None
    _current_session_id: Optional[str] = None
    _current_context: Optional[BrowserContext] = None
    _current_page: Optional[Page] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserEngine, cls).__new__(cls)
        return cls._instance

    async def initialize_session(self, auth_tag: Optional[str] = None) -> Dict[str, str]:
        """
        Initializes a new browser session and connects Playwright to it.
        Args:
            auth_tag: If provided (e.g., 'twitter'), loads the saved storage state.
        """
        # 1. Create Steel Session
        session = session_manager.create_session()
        if not session:
            raise Exception("Failed to create Steel.dev session")
            
        self._current_session_id = session['session_id']
        ws_url = session['websocket_url']
        viewer_url = session['session_viewer_url']
        
        logger.info(f"Connecting to Steel.dev session: {self._current_session_id}")
        
        # 2. Connect Playwright
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.connect_over_cdp(ws_url)
        
        # 3. Create Context (Load Auth if available)
        if auth_tag:
            from .auth import auth_manager
            state_path = auth_manager.get_state_path_if_exists(auth_tag)
            if state_path:
                logger.info(f"Loading auth state for {auth_tag} from {state_path}")
                # Note: connect_over_cdp returns a browser, we create context with storage_state
                self._current_context = await self._browser.new_context(storage_state=state_path)
            else:
                logger.warning(f"Auth state for {auth_tag} not found. Creating fresh context.")
                self._current_context = await self._browser.new_context()
        else:
            self._current_context = self._browser.contexts[0] if self._browser.contexts else await self._browser.new_context()
            
        self._current_page = await self._current_context.new_page()
        
        return {
            "session_id": self._current_session_id,
            "viewer_url": viewer_url
        }

    async def get_page(self) -> Page:
        """Returns the current page, ensuring session is initialized."""
        if not self._current_page or not self._current_page.is_closed() is False:
             await self.initialize_session()
        return self._current_page

    async def close(self):
        """Closes browser and releases session."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        if self._current_session_id:
            session_manager.release_session(self._current_session_id)
            self._current_session_id = None
            
    async def visit(self, url: str):
        """Navigates to a URL with improved waiting logic."""
        page = await self.get_page()
        try:
            logger.info(f"Navigating to {url}")
            # Use 'domcontentloaded' for faster return than 'networkidle'
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            raise e

    async def screenshot(self) -> bytes:
        """Takes a full page screenshot."""
        page = await self.get_page()
        return await page.screenshot(full_page=True)

browser_engine = BrowserEngine()
