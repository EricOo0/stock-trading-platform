import re
import urllib.parse
from typing import Tuple

def detect_market(symbol: str) -> Tuple[str, str]:
    """
    Detect which market the stock belongs to based on symbol format.
    Returns: (market, normalized_symbol)
    
    Markets:
    - 'US': American stocks (e.g., AAPL, TSLA)
    - 'HK': Hong Kong stocks (e.g., 0700.HK, 9988.HK)
    - 'A-SHARE': Chinese A-shares (e.g., 600036.SS, 000001.SZ)
    """
    symbol = urllib.parse.unquote(symbol)
    
    match = re.search(r'\((.*?)\)', symbol)
    if match:
        symbol = match.group(1)
        
    symbol_upper = symbol.upper().strip()
    
    # Hong Kong stocks
    if '.HK' in symbol_upper:
        return ('HK', symbol_upper)
    
    # A-shares (Shanghai/Shenzhen)
    if '.SS' in symbol_upper or '.SZ' in symbol_upper:
        # Extract the base code for AkShare (e.g., 600036.SS -> 600036)
        base_code = symbol_upper.split('.')[0]
        return ('A-SHARE', base_code)
    
    # Check if it's a pure number (likely Chinese stock without suffix)
    if symbol.isdigit():
        if len(symbol) == 6:
            # Could be A-share or HK
            if symbol.startswith('6'):
                return ('A-SHARE', symbol)  # Shanghai
            elif symbol.startswith(('0', '3', '8')): # 8 is Beijing Stock Exchange
                return ('A-SHARE', symbol)  # Shenzhen/Beijing
            else:
                return ('HK', f"{symbol}.HK")  # Hong Kong (rarely 6 digits)
        
        elif len(symbol) == 5:
            # HK Stock (standard 5 digits)
            return ('HK', f"{symbol}.HK")
            
        elif len(symbol) == 4:
            # HK Stock (short format)
            # Usually padded with 0 for 5 digits, but Yahoo uses 4 digits + .HK often? 
            # Actually Yahoo uses 0700.HK. 
            # Let's normalize to 4 digits + .HK if it starts with non-zero?
            # Or just keep it as is + .HK.
            # For AkShare we need 5 digits.
            return ('HK', f"{symbol}.HK")
    
    # Default to US stock
    return ('US', symbol_upper)
