
import logging
from typing import List, Dict, Any, Optional
from tavily import TavilyClient

logger = logging.getLogger(__name__)

class TavilyTool:
    """
    Tavily Web Search Tool
    """
    
    def __init__(self, api_key: str):
        self.client = TavilyClient(api_key=api_key)

    def search(self, query: str, max_results: int = 5, topic: str = "general", days: int = 3) -> List[Dict[str, Any]]:
        """
        Search the web using Tavily.
        """
        try:
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
                if score < 0.3: continue
                    
                results.append({
                    'title': res.get('title', 'No Title'),
                    'href': res.get('url', ''),
                    'body': res.get('content', 'No Content'),
                    'score': score
                })
            
            results.sort(key=lambda x: x['score'], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Tavily search failed: {str(e)}")
            return []

if __name__ == "__main__":
    # Test (requires API key)
    # import os
    # tool = TavilyTool(os.getenv("TAVILY_API_KEY"))
    # print(tool.search("AAPL stock news", topic="news"))
    pass
