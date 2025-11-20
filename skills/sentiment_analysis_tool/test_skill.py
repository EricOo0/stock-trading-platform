#!/usr/bin/env python3
"""
Standalone test script for sentiment analysis skill
"""
import sys
from pathlib import Path

# Add skills directory to path
skills_dir = Path(__file__).parent.parent
sys.path.insert(0, str(skills_dir))

from sentiment_analysis_tool.skill import main_handle

def test_sentiment_skill():
    """Test the sentiment analysis skill"""
    
    print("=" * 60)
    print("Testing Sentiment Analysis Skill")
    print("=" * 60)
    
    test_queries = [
        "Analyze sentiment for AAPL",
        "What's the market sentiment of 000001?",
        "Sentiment analysis for TSLA"
    ]
    
    for query in test_queries:
        print(f"\n\nQuery: {query}")
        print("-" * 60)
        
        result = main_handle(query)
        
        print(f"Status: {result.get('status')}")
        print(f"Symbol: {result.get('symbol')}")
        
        if result.get('status') == 'success':
            data = result.get('data', {})
            print(f"\nSentiment Score: {data.get('score')}/100")
            print(f"Rating: {data.get('rating')}")
            print(f"Summary: {data.get('summary')}")
            print(f"\nKey Drivers:")
            for driver in data.get('key_drivers', []):
                print(f"  - {driver}")
            print(f"\nNews Count: {data.get('news_count')}")
            print(f"\nRecent News (Top 3):")
            for news in data.get('recent_news', []):
                print(f"  • {news['title']}")
                print(f"    Source: {news['source']}, Published: {news['published_at']}")
        else:
            print(f"Error: {result.get('message')}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_sentiment_skill()
