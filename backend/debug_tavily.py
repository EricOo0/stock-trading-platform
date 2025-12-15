import sys
import os
import logging
from pprint import pprint

# Ensure backend root is in path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO)

from backend.infrastructure.search.tavily import TavilyTool
from backend.infrastructure.config.loader import config

if __name__ == "__main__":
    print("Testing TavilyTool Raw...")
    api_key = config.get_api_key("tavily")
    if not api_key:
        print("Error: No Tavily API key found.")
        sys.exit(1)
        
    tool = TavilyTool(api_key)
    # query = "Apple" 
    query = "AAPL"
    try:
        results = tool.search(query, topic="news", days=1)
        print(f"--- Final Results: {len(results)} ---")
        pprint(results)
    except Exception as e:
        print(f"Error: {e}")
