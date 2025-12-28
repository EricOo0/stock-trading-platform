import sys
import os
import logging
import json

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.infrastructure.search.snscrape_tool import SocialScraperTool

def test_scraper(query="Tesla"):
    logging.basicConfig(level=logging.INFO)
    print(f"\n>>> Running snscrape test for: {query}")
    
    scraper = SocialScraperTool()
    
    # 1. Test Twitter
    print("\n--- Testing Twitter Scraper ---")
    twitter_data = scraper.scrape_twitter(query, limit=3)
    print(f"Found {len(twitter_data)} tweets.")
    if twitter_data:
        print(f"Sample Content: {twitter_data[0]['content'][:100]}...")

    # 2. Test Reddit
    print("\n--- Testing Reddit Scraper ---")
    reddit_data = scraper.scrape_reddit(query, limit=3)
    print(f"Found {len(reddit_data)} posts.")
    if reddit_data:
        print(f"Sample Content: {reddit_data[0]['content'][:100]}...")

    # 3. Test All
    print("\n--- Testing Aggregated Search ---")
    all_data = scraper.search_all(query, limit_per_platform=2)
    print(f"Total results: {len(all_data)}")
    
    if all_data:
        print("\nFinal structured output sample:")
        print(json.dumps(all_data[:2], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    search_query = sys.argv[1] if len(sys.argv) > 1 else "Nvidia"
    test_scraper(search_query)
