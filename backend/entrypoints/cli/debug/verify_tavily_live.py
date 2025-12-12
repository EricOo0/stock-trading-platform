
import sys
import os
import json
from tools.registry import Tools

# Force load config from file if possible or rely on env
# assuming config is fixed now

def verify_tavily():
    tools = Tools()
    query = "alibaba"
    print(f"Testing search for: {query}")
    try:
        results = tools.search_market_news(query, provider="tavily")
        print(f"Type of results: {type(results)}")
        print(f"Length of results: {len(results)}")
        if results:
            print(f"First item type: {type(results[0])}")
            print(f"First item keys: {results[0].keys()}")
            # Try to serialize to JSON to check for non-serializable objects
            json_str = json.dumps(results)
            print("serialization successful")
        else:
            print("No results found (check API key)")
            
    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_tavily()
