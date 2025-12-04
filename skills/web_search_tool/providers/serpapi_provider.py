import os
from typing import List, Dict, Any
from serpapi import GoogleSearch
from .base import WebSearchProvider
from utils.logging import logger

class SerpApiProvider(WebSearchProvider):
    """SerpApi search provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "serpapi"

    def search(self, query: str, max_results: int = 50, **kwargs) -> List[Dict[str, Any]]:
        try:
            logger.info(f"Searching with SerpApi: {query}")
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": max_results,
                "engine": "google"
            }
            
            # Handle time limit
            if 'days' in kwargs:
                days = kwargs['days']
                if days <= 1:
                    params["tbs"] = "qdr:d"
                elif days <= 7:
                    params["tbs"] = "qdr:w"
                elif days <= 31:
                    params["tbs"] = "qdr:m"
                else:
                    params["tbs"] = "qdr:y"

            # Handle topic (Google News tab) if topic='news'
            if kwargs.get('topic') == 'news':
                 params["tbm"] = "nws"

            search = GoogleSearch(params)
            results = search.get_dict()
            
            organic_results = results.get("organic_results", [])
            formatted_results = []
            
            for res in organic_results:
                formatted_results.append({
                    'title': res.get('title', 'No Title'),
                    'href': res.get('link', ''),
                    'body': res.get('snippet', 'No Content')
                })
                
            return formatted_results
        except Exception as e:
            logger.error(f"SerpApi search failed: {str(e)}")
            raise e
