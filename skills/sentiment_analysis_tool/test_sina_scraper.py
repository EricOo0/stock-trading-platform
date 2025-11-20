#!/usr/bin/env python3
"""
Test script for Sina Finance scraper
"""
import sys
from pathlib import Path

# Add skills directory to path
skills_dir = Path(__file__).parent.parent
sys.path.insert(0, str(skills_dir))

from sentiment_analysis_tool.services.sina_scraper import SinaFinanceScraper

def test_sina_scraper():
    """Test Sina Finance scraper with various stocks"""
    
    scraper = SinaFinanceScraper()
    
    test_symbols = [
        ("000001", "平安银行 (A股)"),
        ("600519", "贵州茅台 (A股)"),
        ("sh600519", "贵州茅台 (带前缀)"),
        ("sz000001", "平安银行 (带前缀)")
    ]
    
    print("=" * 70)
    print("Testing Sina Finance Scraper")
    print("=" * 70)
    
    for symbol, name in test_symbols:
        print(f"\n\n📊 Testing: {name} ({symbol})")
        print("-" * 70)
        
        try:
            news_items = scraper.scrape_news(symbol, limit=5)
            
            if news_items:
                print(f"✅ Found {len(news_items)} news items:")
                for i, item in enumerate(news_items, 1):
                    print(f"\n{i}. {item['title']}")
                    print(f"   Source: {item['source']}")
                    print(f"   Time: {item.get('published_at', 'N/A')}")
                    print(f"   URL: {item.get('url', 'N/A')[:80]}...")
            else:
                print("❌ No news found")
                print("   This could mean:")
                print("   - Website structure changed")
                print("   - Symbol format incorrect")
                print("   - Rate limiting / blocked")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_sina_scraper()
