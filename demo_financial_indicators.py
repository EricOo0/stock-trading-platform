import sys
import os
import json
# from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

try:
    from skills.financial_report_tool.skill import FinancialReportSkill
except ImportError as e:
    print(f"Error importing FinancialReportSkill: {e}")
    # sys.exit(1)

def test_financial_indicators():
    print("Initializing FinancialReportSkill...")
    skill = FinancialReportSkill()
    
    # Test cases
    test_cases = [
        ("001696", "A-SHARE (Shenzhen Main Board New Code)"),
        ("600036", "A-SHARE (Shanghai)"),
        ("AAPL", "US"),
        ("0700.HK", "HK")
    ]
    
    for symbol, desc in test_cases:
        print(f"\nTesting {symbol} ({desc})...")
        try:
            result = skill.get_financial_indicators(symbol, years=3, use_cache=False)
            
            if result.get("status") == "success":
                print(f"✅ Successfully fetched indicators for {symbol}")
                print(f"   Data Source: {result.get('data_source')}")
                print(f"   Market: {result.get('market')}")
                
                indicators = result.get("indicators", {})
                revenue = indicators.get("revenue", {})
                profit = indicators.get("profit", {})
                
                print(f"   Revenue YoY: {revenue.get('revenue_yoy')}%")
                print(f"   Net Margin: {profit.get('net_margin')}%")
            else:
                print(f"❌ Failed to fetch indicators for {symbol}: {result.get('message')}")
                
        except Exception as e:
            print(f"❌ Exception testing {symbol}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_financial_indicators()
