
import asyncio
import logging
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, BrowserContext, Page, Browser
from backend.infrastructure.config.loader import config
from .session_manager import session_manager

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

    async def initialize_session(self, session_id: Optional[str] = None) -> Dict[str, str]:
        """
        Initializes a browser session.
        Args:
            session_id: If provided, attaches to this existing session (Handoff mode).
                        If None, creates a NEW session.
        """
        if session_id:
            # Attach Mode
            self._current_session_id = session_id
            # Retrieve session details (reconstruct WS url)
            api_key = session_manager.api_key
            ws_url = f"wss://connect.steel.dev?apiKey={api_key}&sessionId={session_id}"
            viewer_url = f"https://app.steel.dev/sessions/{session_id}" # Best guess if not available
            
            logger.info(f"Attaching to existing Steel session: {self._current_session_id}")
        else:
            # Create Mode
            session = session_manager.create_session()
            if not session:
                raise Exception("Failed to create Steel.dev session")
                
            self._current_session_id = session['session_id']
            ws_url = session['websocket_url']
            viewer_url = session['session_viewer_url']
            logger.info(f"Created new Steel session: {self._current_session_id}")
        
        # Connect Playwright
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.connect_over_cdp(ws_url)
        
        # Attach to the existing context if possible, or create new
        if self._browser.contexts:
            self._current_context = self._browser.contexts[0]
        else:
            self._current_context = await self._browser.new_context()
            
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
