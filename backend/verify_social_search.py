import sys
import os
import logging
from pprint import pprint

# Ensure backend root is in path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO)

from backend.app.agents.news_sentiment.tools import search_web

if __name__ == "__main__":
    print("Testing Social Search Logic...")
    
    # Test 1: Normal Search
    print("\n--- Test 1: Normal News Search ---")
    res1 = search_web("AAPL stock news")
    # print(res1[:200])
    
    # Test 2: Social Search (Reddit)
    print("\n--- Test 2: Reddit Search (Should use include_domains) ---")
    res2 = search_web("AAPL sentiment site:reddit.com")
    print(res2[:500])
    
    # Test 3: Social Search (Twitter)
    print("\n--- Test 3: Twitter Search ---")
    res3 = search_web("AAPL site:twitter.com")
    print(res3[:500])
