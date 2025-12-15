
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

    def search(self, query: str, max_results: int = 10, topic: str = "general", days: int = 10, include_domains: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search the web using Tavily.
        """
        try:
            logger.info(f"Searching with Tavily: {query}, topic={topic}, days={days}, domains={include_domains}")
            
            search_params = {
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": True
            }

            if include_domains:
                search_params["include_domains"] = include_domains
            
            if topic == 'news':
                search_params['topic'] = 'news'
                search_params['days'] = days
            
            response = self.client.search(**search_params)
            
            results = []
            raw_results = response.get('results', [])
            logger.info(f"Tavily Raw Response Count: {len(raw_results)}")
            
            # Reverting to 0.3 based on quality analysis. 
            # Relevant news had score > 0.9, noise was < 0.2.
            threshold = 0.3 
            
            for res in raw_results:
                score = res.get('score', 0)
                if score < threshold: 
                    logger.debug(f"Skipping low score result: {res.get('title')} (Score: {score})")
                    continue
                    
                results.append({
                    'title': res.get('title', 'No Title'),
                    'href': res.get('url', ''),
                    'body': res.get('content', 'No Content'),
                    'score': score
                })
            
            results.sort(key=lambda x: x['score'], reverse=True)
            
            if results:
                logger.info(f"Searching with Result: {results[0].keys()}")
                # logger.info(f"Searching with Result value: {str(results[0].values())[:200]}")
            else:
                logger.warning(f"Tavily search returned no results for query: {query}")

            # print(response)
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
