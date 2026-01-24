import os
import argparse
import json
import logging
from typing import List, Dict, Any, Optional
from tavily import TavilyClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSearchSkill:
    """
    Web Search Skill using Tavily
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            api_key = os.getenv("TAVILY_API_KEY")
        
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is not set and no key was provided.")
            
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
            else:
                logger.warning(f"Tavily search returned no results for query: {query}")

            return results
            
        except Exception as e:
            logger.error(f"Tavily search failed: {str(e)}")
            return []

def main():
    parser = argparse.ArgumentParser(description="Web Search Skill")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--max_results", type=int, default=10, help="Maximum number of results")
    parser.add_argument("--topic", type=str, default="general", choices=["general", "news"], help="Search topic")
    parser.add_argument("--days", type=int, default=10, help="Number of days for news search")
    parser.add_argument("--domains", type=str, nargs="*", help="List of domains to include")
    
    args = parser.parse_args()
    
    try:
        skill = WebSearchSkill()
        results = skill.search(
            query=args.query,
            max_results=args.max_results,
            topic=args.topic,
            days=args.days,
            include_domains=args.domains
        )
        print(json.dumps(results, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Error executing skill: {e}")
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
