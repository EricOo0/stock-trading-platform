
import logging
import os
from typing import List, Dict, Any, Optional
from serpapi import GoogleSearch

logger = logging.getLogger(__name__)

class SerpAppTool:
    """
    SerpApi Search Tool
    Uses Google Search via SerpApi.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, query: str, max_results: int = 10, topic: str = "general", days: int = 30) -> List[Dict[str, Any]]:
        """
        Search the web using SerpApi (Google).
        """
        try:
            logger.info(f"Searching with SerpApi: {query}, topic={topic}, days={days}")
            
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": max_results,
                "engine": "google"
            }
            
            # Handle time limits
            if days <= 1:
                params["tbs"] = "qdr:d"
            elif days <= 7:
                params["tbs"] = "qdr:w"
            elif days <= 30:
                params["tbs"] = "qdr:m"
            else:
                 params["tbs"] = "qdr:y"

            # Handle topic (News)
            if topic == 'news':
                 params["tbm"] = "nws"

            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Organic results vs News results
            raw_items = []
            if topic == 'news':
                raw_items = results.get("news_results", [])
            else:
                raw_items = results.get("organic_results", [])
            
            formatted_results = []
            for res in raw_items:
                formatted_results.append({
                    'title': res.get('title', 'No Title'),
                    'href': res.get('link', ''),
                    'body': res.get('snippet', 'No Content')
                })
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"SerpApi search failed: {str(e)}")
            return []
