import sys
import json
import logging
from skill import FinancialReportSkill

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_skill")

def test_financial_indicators():
    skill = FinancialReportSkill()
    
    print("\n=== Test 1: US Stock (AAPL) ===")
    try:
        res = skill.get_financial_indicators("AAPL", market="US")
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"AAPL Test Failed: {e}")

    print("\n=== Test 2: A-share Stock (600036) ===")
    try:
        res = skill.get_financial_indicators("600036", market="A-share")
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"600036 Test Failed: {e}")

def test_report_search():
    skill = FinancialReportSkill()
    
    print("\n=== Test 3: Search US Report (AAPL) ===")
    try:
        res = skill.search_reports("AAPL", market="US")
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"AAPL Search Failed: {e}")

if __name__ == "__main__":
    test_financial_indicators()
    # test_report_search() # Optional, might require EDGAR identity/network
