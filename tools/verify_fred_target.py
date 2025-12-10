
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from tools.market.fred import FredTool
from tools.config import ConfigLoader

# Set up simple environment
config = ConfigLoader.load_config()
api_key = config.get('api_keys', {}).get('fred_api_key', '')
os.environ["FRED_API_KEY"] = api_key

fred = FredTool(api_key=api_key)

# Check Target Rate Series
# DFEDTAR - Fed Funds Target Rate (Discontinued/Changed)
# DFEDTARU - Upper Limit
# DFEDTARL - Lower Limit
series_to_check = ['DFEDTARU', 'DFEDTARL', 'DFF']

for s in series_to_check:
    print(f"Checking {s}...")
    try:
        # Fetch last 1 year to ensure we get latest
        data = fred.get_data(s, observation_start="2024-01-01")
        if data and len(data) > 0:
            print(f"Latest {s}: {data[-1]}")
        else:
            print(f"No data for {s}")
    except Exception as e:
        print(f"Error {s}: {e}")
