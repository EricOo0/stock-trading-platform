"""
Test script for WebSearchSkill to verify DuckDuckGo functionality
"""
import sys
import os

# Add the project root and agent directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'agent'))

from skills.web_search_tool.skill import WebSearchSkill
from utils.logging import logger

def test_web_search():
    """Test DuckDuckGo search with various queries"""
    
    print("=" * 80)
    print("🔍 Testing DuckDuckGo Web Search")
    print("=" * 80)
    
    # Initialize the skill
    skill = WebSearchSkill(tavily_api_key="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")
    
    # Test queries
    test_queries = [
        "Python programming tutorial",
        "NVIDIA stock news 2024",
        "artificial intelligence latest developments",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_queries)}: {query}")
        print(f"{'='*80}")
        
        try:
            result = skill._run(query)
            
            if result["status"] == "success":
                print(f"✅ SUCCESS")
                print(f"Query: {result['query']}")
                print(f"\nResults:")
                print(result['result'][:500])  # Print first 500 chars
                
                if result.get('raw_results'):
                    print(f"\n📊 Found {len(result['raw_results'])} results")
                else:
                    print(f"\n⚠️  No raw results returned")
            else:
                print(f"❌ FAILED")
                print(f"Status: {result['status']}")
                print(f"Message: {result.get('message', 'No error message')}")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
        
        print()
    
    print("=" * 80)
    print("Test completed!")
    print("=" * 80)

if __name__ == "__main__":
    test_web_search()
