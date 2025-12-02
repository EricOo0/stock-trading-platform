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

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        try:
            logger.info(f"Searching with Tavily: {query}")
            response = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=True
            )
            
            results = []
            
            # Add the generated answer as the first result if available
            if response.get('answer'):
                results.append({
                    'title': 'Tavily AI Answer',
                    'href': '',
                    'body': response['answer']
                })

            for res in response.get('results', []):
                results.append({
                    'title': res.get('title', 'No Title'),
                    'href': res.get('url', ''),
                    'body': res.get('content', 'No Content')
                })
            
            return results
        except Exception as e:
            logger.error(f"Tavily search failed: {str(e)}")
            raise e
