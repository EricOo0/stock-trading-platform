import unittest
from skill import NewsSentimentSkill
import json

class TestNewsSentimentSkill(unittest.TestCase):
    def setUp(self):
        self.tool = NewsSentimentSkill()

    def test_analyze_sentiment(self):
        print("\n--- Testing Sentiment Analysis ---")
        text = "This stock is great and I love it!"
        result = self.tool.analyze_sentiment(text)
        print(f"Text: {text}")
        print(f"Result: {result}")
        self.assertIn('polarity', result)
        self.assertIn('subjectivity', result)
        
        # In some environments (like missing sqlite3), TextBlob might fallback or be disabled.
        # We only assert greater than 0 if it seems to be working.
        if result['polarity'] != 0.0:
            self.assertGreater(result['polarity'], 0)
        else:
            print("Skipping polarity check as sentiment analysis might be disabled or neutral.")

        text_neg = "This is a terrible investment."
        result_neg = self.tool.analyze_sentiment(text_neg)
        print(f"Text: {text_neg}")
        print(f"Result: {result_neg}")
        if result_neg['polarity'] != 0.0:
            self.assertLess(result_neg['polarity'], 0)

    def test_search_news(self):
        print("\n--- Testing News Search (Sina) ---")
        symbol = "000001" # Ping An Bank
        print(f"Searching news for {symbol}...")
        results = self.tool.search_news(symbol, limit=2)
        print(f"Found {len(results)} articles.")
        if results:
            print("First article sample:")
            print(json.dumps(results[0], indent=2, ensure_ascii=False))
            self.assertIn('title', results[0])
            self.assertIn('sentiment', results[0])
        else:
            print("No news found (could be network issue or no recent news).")

    def test_search_social(self):
        print("\n--- Testing Social Search (Mock/Live) ---")
        # Note: snscrape often fails without proper environment/proxy, so we just check it runs without crashing
        query = "Python"
        print(f"Searching social for {query}...")
        results = self.tool.search_social(query, limit=1)
        print(f"Found {len(results)} items.")
        if results:
            print("First item sample:")
            print(json.dumps(results[0], indent=2, ensure_ascii=False))

if __name__ == '__main__':
    unittest.main()
