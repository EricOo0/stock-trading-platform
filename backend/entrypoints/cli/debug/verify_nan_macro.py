
import sys
import os
import json
import math

# Add project root to path
sys.path.append(os.getcwd())

from tools.registry import Tools

def has_nan(obj):
    if isinstance(obj, float):
        return math.isnan(obj)
    if isinstance(obj, dict):
        return any(has_nan(v) for v in obj.values())
    if isinstance(obj, list):
        return any(has_nan(i) for i in obj)
    return False

def check_indicator(ind):
    print(f"Checking {ind}...")
    try:
        tools = Tools()
        data = tools.get_macro_history(ind, '1y')
        if has_nan(data):
            print(f"FAIL: {ind} contains NaN values!")
            # Print sample
            print(json.dumps(data, default=str)[:200])
        else:
            print(f"PASS: {ind} is clean.")
    except Exception as e:
        print(f"ERROR: {ind} failed: {e}")

if __name__ == "__main__":
    check_indicator('CN_PPI')
    check_indicator('CN_LPR')
