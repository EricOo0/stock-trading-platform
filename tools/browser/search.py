from typing import List, Dict, Any
from .engine import browser_engine
import logging

logger = logging.getLogger(__name__)

async def browser_search(query: str, engine: str = 'google') -> List[Dict[str, Any]]:
    """
    Performs a search using the real browser to bypass API limitations 
    and potentially capture AI overviews/rich snippets.
    
    Args:
        query: Search query
        engine: Search engine ('google' or 'bing')
        
    Returns:
        List of results with title, link, snippet
    """
    if engine.lower() == 'google':
        url = f"https://www.google.com/search?q={query}"
    else:
        url = f"https://www.bing.com/search?q={query}"
        
    try:
        await browser_engine.visit(url)
        page = await browser_engine.get_page()
        
        # Simple extraction logic (can be enhanced with lxml/BeautifulSoup)
        # Google search results container: #search or #rso
        results = []
        
        # Determine selectors based on engine
        if engine.lower() == 'google':
             # Main results
            elements = await page.locator('#rso > div').all()
            for el in elements:
                # Extract Title
                title_el = el.locator('h3')
                link_el = el.locator('a')
                snippet_el = el.locator('div[style*="-webkit-line-clamp"]') # Rough heuristic
                
                if await title_el.count() > 0 and await link_el.count() > 0:
                    title = await title_el.first.text_content()
                    link = await link_el.first.get_attribute('href')
                    
                    if link and title:
                        results.append({
                            "title": title,
                            "link": link,
                            "snippet": "" # Simplified for now
                        })
        
        logger.info(f"Browser search found {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Browser search failed: {e}")
        return []

