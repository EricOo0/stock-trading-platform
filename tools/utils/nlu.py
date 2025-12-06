
import re
from typing import List, Optional

def extract_symbols(text: str) -> List[str]:
    """
    Extract stock symbols from text using regex and keyword matching.
    Supports A-share (6 digits), US (1-5 letters), HK (5 digits), and common Chinese company names.
    """
    symbols = []
    text_clean = text.upper()

    # Chinese company name mapping
    chinese_company_mapping = {
        # US
        '苹果': 'AAPL', '微软': 'MSFT', '谷歌': 'GOOGL', '亚马逊': 'AMZN',
        '特斯拉': 'TSLA', '英伟达': 'NVDA', 'META': 'META',
        '阿里巴巴': 'BABA', '百度': 'BIDU', '京东': 'JD', '拼多多': 'PDD',
        
        # A-share
        '平安银行': '000001', '招商银行': '600036', '贵州茅台': '600519', 
        '五粮液': '000858', '中国平安': '601318', '宁德时代': '300750',
        
        # HK
        '腾讯': '00700', '腾讯控股': '00700', '美团': '03690', '小米': '01810',
    }

    # 1. Match company names
    for company_name, symbol in chinese_company_mapping.items():
        if company_name in text:
            symbols.append(symbol)

    # 2. Match Codes
    
    # A-share: 6 digits (simplified check, more strict validation in tool)
    # Common prefixes: 000, 001, 002, 300, 600, 601, 603, 688
    a_share_matches = re.findall(r'\b(00\d{4}|30\d{4}|60\d{4}|68\d{4})\b', text_clean)
    symbols.extend(a_share_matches)

    # HK: 5 digits, usually starts with 0
    hk_matches = re.findall(r'\b(0\d{4})\b', text_clean)
    symbols.extend(hk_matches)

    # US: 1-5 Capital Letters
    # Need to be careful not to match common words like 'A', 'I', 'AM' if they appear alone?
    # Context usually helps, but here we just grab candidates.
    # We filter out common words if needed, but for now apply simple regex.
    # Exclude "AND", "OR", "THE" etc if they were upper case in input.
    # But usually stock symbols are distinct.
    us_matches = re.findall(r'\b([A-Z]{1,5})\b', text_clean)
    
    # Filter common stop words if they appear as "symbols"
    STOP_WORDS = {'AND', 'OR', 'THE', 'FOR', 'IN', 'OF', 'TO', 'AT', 'IS', 'IT', 'BY', 'MY', 'HI', 'OK'}
    
    for match in us_matches:
        if match not in STOP_WORDS and match not in symbols: # Avoid dups
             # Heuristic: US symbols usually don't mix with digits in this regex
             symbols.append(match)

    # Dedup and preserve order
    seen = set()
    unique_symbols = []
    for s in symbols:
        if s not in seen:
            seen.add(s)
            unique_symbols.append(s)
            
    return unique_symbols[:10] # Limit to 10
