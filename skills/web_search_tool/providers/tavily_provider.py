import os
from typing import List, Dict, Any
from tavily import TavilyClient
from .base import WebSearchProvider
from utils.logging import logger

class TavilyProvider(WebSearchProvider):
    """Tavily search provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = TavilyClient(api_key=api_key)

    @property
    def name(self) -> str:
        return "tavily"

    def search(self, query: str, max_results: int = 50, **kwargs) -> List[Dict[str, Any]]:
        try:
            topic = kwargs.get('topic', 'general')
            days = kwargs.get('days', 15)
            
            logger.info(f"Searching with Tavily: {query}, topic={topic}, days={days}")
            
            search_params = {
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": True
            }
            
            if topic == 'news':
                search_params['topic'] = 'news'
                search_params['days'] = days
            
            response = self.client.search(**search_params)
            
            results = []
            
            for res in response.get('results', []):
                score = res.get('score', 0)
                if score < 0.3:
                    continue
                    
                results.append({
                    'title': res.get('title', 'No Title'),
                    'href': res.get('url', ''),
                    'body': res.get('content', 'No Content'),
                    'score': score
                })
            
            # Sort by score descending
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return results
        except Exception as e:
            logger.error(f"Tavily search failed: {str(e)}")
            raise e
