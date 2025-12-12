import logging
from .engine import browser_engine

logger = logging.getLogger(__name__)

async def visit(url: str, timeout: int = 60000):
    """
    High-level action to visit a URL.
    """
    await browser_engine.visit(url)

async def screenshot() -> bytes:
    """
    High-level action to take a screenshot.
    """
    return await browser_engine.screenshot()

async def get_content(selector: str = "body") -> str:
    """
    Gets the text content of a specific element.
    """
    page = await browser_engine.get_page()
    try:
        if selector == "body":
            return await page.content() # Return full HTML
        else:
             element = page.locator(selector).first
             return await element.text_content()
    except Exception as e:
        logger.error(f"Failed to get content for {selector}: {e}")
        return ""
