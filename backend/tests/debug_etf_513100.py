
from backend.infrastructure.market.sina import SinaFinanceTool
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

tool = SinaFinanceTool()
try:
    # 513100
    print("Querying 513100 via Sina...")
    quote = tool.get_stock_quote("513100", "A-share")
    print(f"513100 Quote: {quote}")

    # 513050
    print("\nQuerying 513050 via Sina...")
    quote_kweb = tool.get_stock_quote("513050", "A-share")
    print(f"513050 Quote: {quote_kweb}")
except Exception as e:
    print(f"Error: {e}")
