import sys
import os
sys.path.append(os.getcwd())
from tools.registry import Tools

def test_macro_data():
    tools = Tools()
    
    # Frontend config IDs
    indicators = [
        # China
        "CN_GDP", "CN_CPI", "CN_PMI", "CN_PPI", "CN_M2", "CN_LPR",
        # Global (US)
        "US10Y", "VIX", "DXY", "US_CPI", "UNEMPLOYMENT", "NONFARM", "FED_FUNDS"
    ]
    
    print(f"{'Indicator':<15} | {'Source':<10} | {'Status':<10} | {'Data Points'}")
    print("-" * 60)
    
    for indicator in indicators:
        try:
            # Emulate how API calls it
            result = tools.get_macro_history(indicator)
            
            status = "OK"
            data_points = 0
            source = "Unknown"
            
            if "error" in result:
                status = "ERROR"
                data_points = result["error"]
            elif "data" in result and result["data"]:
                status = "SUCCESS"
                data_points = len(result["data"])
                # Try to guess source from internal tool state if possible, or just logic
                if "FRED" in str(result): source = "FRED" 
                # This check is weak, but we just want to see if we get data.
            else:
                status = "EMPTY"
            
            print(f"{indicator:<15} | {source:<10} | {status:<10} | {data_points}")
            
        except Exception as e:
            print(f"{indicator:<15} | ERROR      | EXCEPTION  | {str(e)}")

if __name__ == "__main__":
    test_macro_data()
