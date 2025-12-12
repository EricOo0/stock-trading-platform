
import sys
import os
sys.path.append(os.getcwd())
from tools.registry import Tools
import json

def verify():
    tools = Tools()
    
    print("=== Verifying China Macro Data (AkShare) ===")
    indicators = ["china m2", "china lpr", "china ppi", "china social"]
    for ind in indicators:
        print(f"\nFetching {ind}...")
        data = tools.get_macro_data(ind)
        print(f"Latest: {json.dumps(data, ensure_ascii=False)}")
        
        hist = tools.get_macro_history(ind)
        if "error" not in hist:
            print(f"History (First 2): {hist['data'][:2]}")
        else:
            print(f"History Error: {hist}")

    print("\n=== Verifying US Macro Data (FRED) ===")
    us_indicators = ["unemployment", "nonfarm", "us cpi", "fed funds"]
    for ind in us_indicators:
        print(f"\nFetching {ind}...")
        hist = tools.get_macro_history(ind, period="1y")
        if "error" not in hist:
            print(f"History (First 2): {hist['data'][:2]}")
        else:
            print(f"History Error: {hist}")

if __name__ == "__main__":
    verify()
