
import logging
import os
import time
from typing import List, Dict, Any
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class DuckDuckGoTool:
    """
    DuckDuckGo Search Tool
    Uses 'ddgs' library. No API key required.
    """
    
    def search(self, query: str, max_results: int = 10, topic: str = "general", days: int = 30) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo.
        """
        logger.info(f"Searching with DDG: {query}")
        
        timelimit = None
        if days:
            if days <= 1: timelimit = 'd'
            elif days <= 7: timelimit = 'w'
            elif days <= 31: timelimit = 'm'
            else: timelimit = 'y'
            
        results = []
        backends = ["duckduckgo", "bing", "auto"]
        
        # Simple retry loop
        for backend in backends:
            try:
                # Support proxy if set in env
                proxy = os.getenv("DDGS_PROXY", None)
                ddgs = DDGS(proxy=proxy, timeout=20) if proxy else DDGS(timeout=20)
                
                # 'news' backend if topic is news? DDGS `news` method exists but we use text with backend
                # Actually DDGS has a news() method.
                if topic == 'news':
                    ddgs_gen = ddgs.news(query, max_results=max_results, safesearch="off") # timelimit not supported in news() mostly
                else:
                    ddgs_gen = ddgs.text(query, backend=backend, max_results=max_results, timelimit=timelimit)
                
                if ddgs_gen:
                    for res in ddgs_gen:
                        results.append({
                            'title': res.get('title', 'No Title'),
                            'href': res.get('href', '') or res.get('url', ''),
                            'body': res.get('body', '') or res.get('snippet', 'No Content')
                        })
                    
                    if results: return results # Success
            
            except Exception as e:
                logger.warning(f"DDG search failed with backend {backend}: {e}")
                time.sleep(1)
                continue
                
        return results
