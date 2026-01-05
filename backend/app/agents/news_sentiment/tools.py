import logging
import json
import asyncio
import httpx
import feedparser
from typing import Dict, Any, List, Optional
from backend.app.registry import Tools
# from backend.infrastructure.browser.steel_browser import browser_engine

logger = logging.getLogger(__name__)
tools = Tools()

def search_web(query: str, days: int = 7) -> str:
    """
    DISCOVERY TOOL: Searches the web for *Content Entry Points* (URLs).
    
    Use this to find WHERE to look. Do not rely on the snippets for the final answer.
    Returns a list of relevant URLs with titles.
    """
    try:
        logger.info(f"[NewsSentiment] Executing search_web with query: '{query}'")
        
        # 1. Parse 'site:domain.com' Logic
        import re
        site_pattern = r'site:([\w\.-]+)'
        domains = re.findall(site_pattern, query)
        
        # Clean query if domains found
        clean_query = re.sub(site_pattern, '', query).strip()
        
        # 2. Determine Search Mode
        # If specific domains are targeted (especially social media), use 'general' topic as per best practices
        topic = "news"
        if domains:
            # Check for social media domains that might benefit from 'general' topic
            social_domains = ['reddit.com', 'twitter.com', 'x.com', 'linkedin.com']
            if any(d in social_domains for d in domains):
                topic = "general"
                logger.info(f"[NewsSentiment] Social media search detected. Switched to topic='general', domains={domains}")
            else:
                logger.info(f"[NewsSentiment] Domain restricted search. domains={domains}")
        
        # Use the robust registry search (Tavily/Serp/DDG)
        if domains:
             results = tools.search_market_news(clean_query, topic=topic, include_domains=domains)
        else:
             results = tools.search_market_news(query)
        logger.info(f"[NewsSentiment] Search returned {len(results) if results else 0} results.")
        
        if results:
             # logger.info(f"[NewsSentiment] First result keys: {results[0].keys()}")
             pass
        
        if not results:
            logger.warning(f"[NewsSentiment] No results found for query: '{query}'")
            return f"No results found for query: '{query}'. Try broader keywords or check internet connection."
        
        # Format results strictly as entry points
        formatted = ["DISCOVERY RESULTS (Use inspect_page to read details):"]
        valid_count = 0
        for res in results:
            title = res.get('title', 'Unknown')
            # robustly get URL
            url = res.get('url', res.get('link', res.get('href', ''))).strip()
            
            # Skip invalid URLs
            if not url or url.startswith('http') is False:
                continue

            snippet = res.get('content', res.get('body', ''))[:150] # Short snippet only
            valid_count += 1
            formatted.append(f"[{valid_count}] {title}\n    URL: {url}\n    Hint: {snippet}\n")
            
        if valid_count == 0:
            return "No valid links found in search results."

        return "\n".join(formatted)
    except Exception as e:
        logger.error(f"[NewsSentiment] Search failed: {e}", exc_info=True)
        return f"Error executing search: {e}"

# Function: fetch_reddit_rss
# Complexity: O(N), Cyclomatic=3 (1 try + 1 for loop + error handling)
# Lines: 30
async def fetch_reddit_rss(subreddit: str, category: str = "hot", limit: int = 10) -> str:
    """
    SOCIAL TOOL: Fetches Reddit threads via RSS.
    
    Use this to get realtime/hottest discussions from specific subreddits 
    (e.g., 'wallstreetbets', 'stocks', 'investing', 'AAPL').
    Returns a formatted list of threads with links.
    """
    try:
        url = f"https://www.reddit.com/r/{subreddit}/{category}.rss?limit={limit}"
        logger.info(f"[NewsSentiment] Fetching RSS: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            content = resp.content
            
        feed = feedparser.parse(content)
        
        if not feed.entries:
            return f"No entries found in subreddit '{subreddit}' ({category}). Check if subreddit exists."
            
        output = [f"REDDIT FEED: r/{subreddit} ({category})"]
        for idx, entry in enumerate(feed.entries[:limit], 1):
            title = entry.get('title', 'No Title')
            link = entry.get('link', '')
            published = entry.get('updated', entry.get('published', 'Unknown Date'))
            
            output.append(f"[{idx}] {title}")
            output.append(f"    Date: {published}")
            output.append(f"    Link: {link}\n")
            
        return "\n".join(output)
        
    except Exception as e:
        logger.error(f"[NewsSentiment] RSS Fetch failed: {e}")
        return f"Error fetching RSS for r/{subreddit}: {e}"

async def inspect_page(url: str) -> str:
    """
    INSPECTION TOOL: Inspects a specific URL using simple HTTP fetching.
    Note: Browser automation (Steel) is currently disabled.
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
            # Fallback for Xueqiu if browser is disabled
            return f"Xueqiu inspection via browser is currently disabled. Please use search snippets for '{url}'."

        # Default Handler
        return await _inspect_generic(url)

    except Exception as e:
        logger.error(f"Inspection failed for {url}: {e}")
        return f"Error inspecting page: {e}"

async def _inspect_reddit(url: str) -> str:
    """Handling Reddit with direct JSON API fetch (No Browser)."""
    try:
        # 1. Try JSON Shortcut via HTTP (Fastest/Most Reliable if not blocked)
        target_url = url.split('?')[0]
        if not target_url.endswith('.json'):
            target_url += ".json"
            
        logger.info(f"[NewsSentiment] Fetching Reddit JSON: {target_url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Try HTTP request first
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(target_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 1:
                        post = data[0]['data']['children'][0]['data']
                        comments = data[1]['data']['children']
                        
                        output = f"REDDIT THREAD: {post.get('title')}\n"
                        output += f"Author: {post.get('author')} | Upvotes: {post.get('ups')}\n"
                        output += f"Post Text: {post.get('selftext', '')[:2000]}\n\n"
                        
                        output += "--- TOP COMMENTS ---\n"
                        count = 0
                        for c in comments:
                            if count >= 15: break
                            c_data = c.get('data', {})
                            if 'body' in c_data:
                                output += f"[{c_data.get('author')}] (Score {c_data.get('score')}): {c_data.get('body')[:800]}\n---\n"
                                count += 1
                        return output
                else:
                    logger.warning(f"Reddit JSON fetch failed with status {resp.status_code}")
        except Exception as e:
            logger.warning(f"Reddit HTTP JSON fetch failed: {e}. Falling back to visual.")

        # 2. Visual Fallback (Steel Browser) - only if HTTP fails
        logger.info("Falling back to visual inspection for Reddit...")
        return await _inspect_generic(url, scroll_steps=3)

    except Exception as e:
        return f"Reddit inspection error: {e}"

# async def _inspect_xueqiu(url: str) -> str:
#     """Handling Xueqiu with aggressive scrolling for comments."""
#     try:
#         await browser_engine.visit(url)
#         page = await browser_engine.get_page()
#         
#         # Xueqiu loads comments on scroll.
#         # Scroll down significantly.
#         for _ in range(3):
#             await page.evaluate("window.scrollBy(0, 800)")
#             await asyncio.sleep(1.0) # Wait for hydration
#             
#         # Extract main post and comments
#         # Heuristic: Main content usually in 'article__content' or similar, comments in 'comment-list'
#         # For general robustness, we dump text but formatted.
#         
#         return await page.evaluate("""() => {
#             // Simple text extraction for now, can be optimized with selectors if needed
#             return document.body.innerText;
#         }""")
#     except Exception as e:
#         return f"Xueqiu inspection error: {e}"

async def _inspect_generic(url: str, scroll_steps: int = 1) -> str:
    """Generic page inspection via HTTP GET (Lightweight)."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            
            # Simple text extraction
            # In a real scenario, use readability-lxml or beautifulsoup
            # For now, we return a simple stripped text or raw HTML snippet if too long
            text = resp.text
            
            # Very basic cleanup (this is not perfect but works for simple fallback)
            import re
            text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
            text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text[:15000]
            
    except Exception as e:
        logger.error(f"Generic inspection failed for {url}: {e}")
        return f"Error fetching content: {e}"
