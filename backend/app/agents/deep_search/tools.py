import logging
from typing import Dict, Any, List, Optional
from backend.app.registry import Tools
from backend.infrastructure.browser.steel_browser import browser_engine

logger = logging.getLogger(__name__)
tools = Tools()

def search_web(query: str, days: int = 7) -> str:
    """
    Searches the web for recent discussions and news.
    Args:
        query: The search query (e.g., "AAPL sentiment reddit").
        days: Restrict search to the last N days (default 7).
    Returns:
        A string summary or JSON string of search results.
    """
    try:
        results = tools.search_market_news(query, count=6)
        if not results:
            return "No results found."
        
        # Format results for the agent
        formatted = []
        for i, res in enumerate(results):
            title = res.get('title', 'Unknown')
            url = res.get('url', res.get('link', ''))
            snippet = res.get('content', '')[:300]
            formatted.append(f"[{i+1}] {title}\nURL: {url}\nSnippet: {snippet}\n")
            
        return "\n".join(formatted)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Error executing search: {e}"

async def visit_page(url: str) -> str:
    """
    Visits a URL using the cloud browser.
    Returns the page text content.
    """
    try:
        await browser_engine.visit(url)
        page = await browser_engine.get_page()
        
        # Simple extraction
        content = await page.evaluate("() => document.body.innerText")
        return content[:5000] # Return first 5000 chars to save context
    except Exception as e:
        logger.error(f"Visit failed: {e}")
        return f"Error visiting page: {e}"

async def scroll_page() -> str:
    """Scrolls down the current page to load more content."""
    try:
        page = await browser_engine.get_page()
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        return "Scrolled down."
    except Exception as e:
        return f"Error scrolling: {e}"
