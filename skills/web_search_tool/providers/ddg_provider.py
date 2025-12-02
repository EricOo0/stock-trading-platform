import os
import time
import traceback
from typing import List, Dict, Any
from ddgs import DDGS
from .base import WebSearchProvider
from utils.logging import logger

class DuckDuckGoProvider(WebSearchProvider):
    """DuckDuckGo search provider."""

    @property
    def name(self) -> str:
        return "duckduckgo"

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"Searching with DuckDuckGo: {query}")
        
        results = []
        max_retries = 2
        backends = ["bing", "duckduckgo", "yahoo", "auto"]
        
        for attempt in range(max_retries + 1):
            for backend in backends:
                try:
                    proxy = os.getenv("DDGS_PROXY", None)
                    ddgs = DDGS(proxy=proxy, timeout=20) if proxy else DDGS(timeout=20)
                    
                    logger.info(f"Attempting search with backend: {backend}")
                    ddgs_gen = ddgs.text(query, backend=backend, max_results=max_results)
                    
                    if ddgs_gen:
                        raw_results = list(ddgs_gen)
                        if raw_results:
                            for res in raw_results:
                                results.append({
                                    'title': res.get('title', 'No Title'),
                                    'href': res.get('href', ''),
                                    'body': res.get('body', 'No Content')
                                })
                            return results
                except Exception as e:
                    logger.warning(f"DDGS search failed with backend {backend}: {str(e)}")
                    continue
            
            if attempt < max_retries:
                time.sleep(2)
        
        if not results:
             logger.warning(f"DuckDuckGo returned no results for: {query}")
             
        return results
