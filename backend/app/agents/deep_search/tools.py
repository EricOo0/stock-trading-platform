import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from backend.app.registry import Tools
from backend.infrastructure.browser.steel_browser import browser_engine

logger = logging.getLogger(__name__)
tools = Tools()

def search_web(query: str, days: int = 7) -> str:
    """
    DISCOVERY TOOL: Searches the web for *Content Entry Points* (URLs).
    
    Use this to find WHERE to look. Do not rely on the snippets for the final answer.
    Returns a list of relevant URLs with titles.
    """
    try:
        # Use the robust registry search (Tavily/Serp/DDG)
        results = tools.search_market_news(query)
        if not results:
            return "No results found."
        
        # Format results strictly as entry points
        formatted = ["DISCOVERY RESULTS (Use inspect_page to read details):"]
        valid_count = 0
        for res in results:
            title = res.get('title', 'Unknown')
            # robustly get URL
            url = res.get('url', res.get('link', '')).strip()
            
            # Skip invalid URLs
            if not url or url.startswith('http') is False:
                continue

            snippet = res.get('content', '')[:150] # Short snippet only
            valid_count += 1
            formatted.append(f"[{valid_count}] {title}\n    URL: {url}\n    Hint: {snippet}\n")
            
        if valid_count == 0:
            return "No valid links found in search results."

        return "\n".join(formatted)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Error executing search: {e}"

async def inspect_page(url: str) -> str:
    """
    INSPECTION TOOL: Deeply inspects a specific URL using the cloud browser.
    
    MUST be used for:
    - Reddit threads (Auto-extracts comments)
    - Xueqiu posts (Auto-scrolls for dynamic content)
    - Any news article requiring full reading
    """
    if not url or not url.strip():
        return "Error: Empty URL provided. Please provide a valid URL from the search results."

    print(f"Inspecting: {url}")
    try:
        # Special Handler: Reddit
        if "reddit.com" in url:
            return await _inspect_reddit(url)
            
        # Special Handler: Xueqiu
        if "xueqiu.com" in url:
            return await _inspect_xueqiu(url)

        # Default Handler
        return await _inspect_generic(url)

    except Exception as e:
        logger.error(f"Inspection failed for {url}: {e}")
        return f"Error inspecting page: {e}"

async def _inspect_reddit(url: str) -> str:
    """Handling Reddit with JSON trick or Visual Fallback."""
    try:
        page = await browser_engine.get_page()
        
        # 1. Try JSON Shortcut (Fastest/Most Reliable if not blocked)
        target_url = url.split('?')[0]
        if not target_url.endswith('.json'):
            target_url += ".json"
            
        await page.goto(target_url, wait_until='domcontentloaded')
        content = await page.evaluate("() => document.body.innerText")
        
        try:
            data = json.loads(content)
            if isinstance(data, list) and len(data) > 1:
                post = data[0]['data']['children'][0]['data']
                comments = data[1]['data']['children']
                
                output = f"REDDIT THREAD: {post.get('title')}\n"
                output += f"Author: {post.get('author')} | Upvotes: {post.get('ups')}\n"
                output += f"Post Text: {post.get('selftext', '')[:1000]}\n\n"
                
                output += "--- TOP COMMENTS ---\n"
                count = 0
                for c in comments:
                    if count >= 10: break
                    c_data = c.get('data', {})
                    if 'body' in c_data:
                        output += f"[{c_data.get('author')}] (Score {c_data.get('score')}): {c_data.get('body')[:500]}\n---\n"
                        count += 1
                return output
        except:
            logger.warning("Reddit JSON parse failed, falling back to visual.")

        # 2. Visual Fallback (Steel Browser)
        return await _inspect_generic(url, scroll_steps=3)

    except Exception as e:
        return f"Reddit inspection error: {e}"

async def _inspect_xueqiu(url: str) -> str:
    """Handling Xueqiu with aggressive scrolling for comments."""
    try:
        await browser_engine.visit(url)
        page = await browser_engine.get_page()
        
        # Xueqiu loads comments on scroll.
        # Scroll down significantly.
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(1.0) # Wait for hydration
            
        # Extract main post and comments
        # Heuristic: Main content usually in 'article__content' or similar, comments in 'comment-list'
        # For general robustness, we dump text but formatted.
        
        return await page.evaluate("""() => {
            // Simple text extraction for now, can be optimized with selectors if needed
            return document.body.innerText;
        }""")
    except Exception as e:
        return f"Xueqiu inspection error: {e}"

async def _inspect_generic(url: str, scroll_steps: int = 1) -> str:
    """Generic page inspection with scrolling."""
    await browser_engine.visit(url)
    page = await browser_engine.get_page()
    
    # Scroll to trigger lazy images/content
    for _ in range(scroll_steps):
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await asyncio.sleep(0.5)
        
    content = await page.evaluate("() => document.body.innerText")
    
    # Check for common blocking/security messages
    blocked_keywords = ["blocked", "security", "captcha", "access denied", "403 forbidden", "cloudflare"]
    if any(keyword in content.lower()[:200] for keyword in blocked_keywords):
        return f"Content unavailable: The site blocked the automated inspection ({content[:50]}...)."
        
    return content[:15000] # Return reasonable amount of text
