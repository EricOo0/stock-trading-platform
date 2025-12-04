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
    
    # Remove possible exchange prefix (SH/SZ)
    if symbol_upper.startswith('SH') or symbol_upper.startswith('SZ'):
        symbol_upper = symbol_upper[2:]
    
    # Hong Kong stocks
    if '.HK' in symbol_upper:
        return ('HK', symbol_upper)
    
    # A-shares (Shanghai/Shenzhen)
    if '.SS' in symbol_upper or '.SZ' in symbol_upper:
        # Extract the base code for AkShare (e.g., 600036.SS -> 600036)
        base_code = symbol_upper.split('.')[0]
        return ('A-SHARE', base_code)
    
    # Check if it's a pure number (likely Chinese stock without suffix)
    if symbol_upper.isdigit():
        if len(symbol_upper) == 6:
            # A-share codes:
            # Shanghai: 60xxxx, 68xxxx (科创板)
            # Shenzhen: 00xxxx, 30xxxx (创业板), 001xxx (深圳主板新代码)
            # Beijing: 8xxxxx
            return ('A-SHARE', symbol_upper)
        
        elif len(symbol_upper) == 5:
            # HK Stock (standard 5 digits)
            return ('HK', f"{symbol_upper}.HK")
            
        elif len(symbol_upper) == 4:
            # HK Stock (short format)
            return ('HK', f"{symbol_upper}.HK")
    
    # Default to US stock
    return ('US', symbol_upper)

